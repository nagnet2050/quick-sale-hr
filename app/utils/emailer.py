import smtplib
from email.mime.text import MIMEText
import requests


def _send_via_smtp(app, sender: str, sender_name: str, to_email: str, subject: str, body: str) -> bool:
    server = app.config.get('SMTP_SERVER', '')
    port = app.config.get('SMTP_PORT', 587)
    username = app.config.get('SMTP_USERNAME', '')
    password = app.config.get('SMTP_PASSWORD', '')
    use_tls = app.config.get('SMTP_USE_TLS', True)
    use_ssl = app.config.get('SMTP_USE_SSL', False)

    if not server or not username or not password:
        app.logger.warning('[Email][SMTP] Not configured. Skipping send to %s. Subject: %s Body: %s', to_email, subject, body)
        return False
    try:
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = f"{sender_name} <{sender}>" if sender_name else sender
        msg['To'] = to_email

        if use_ssl:
            with smtplib.SMTP_SSL(server, port, timeout=15) as smtp:
                smtp.login(username, password)
                smtp.sendmail(sender, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(server, port, timeout=15) as smtp:
                if use_tls:
                    smtp.starttls()
                smtp.login(username, password)
                smtp.sendmail(sender, [to_email], msg.as_string())
        return True
    except Exception as e:
        app.logger.error('[Email][SMTP] Failed to send email to %s: %s', to_email, e)
        return False


def _send_via_mailgun(app, sender: str, sender_name: str, to_email: str, subject: str, body: str) -> bool:
    domain = app.config.get('MAILGUN_DOMAIN', '')
    api_key = app.config.get('MAILGUN_API_KEY', '')
    if not domain or not api_key:
        app.logger.warning('[Email][Mailgun] Not configured.')
        return False
    try:
        resp = requests.post(
            f'https://api.mailgun.net/v3/{domain}/messages',
            auth=('api', api_key),
            data={
                'from': f"{sender_name} <{sender}>" if sender_name else sender,
                'to': [to_email],
                'subject': subject,
                'text': body,
            }, timeout=15
        )
        if resp.status_code in (200, 202):
            return True
        app.logger.error('[Email][Mailgun] Failed status=%s body=%s', resp.status_code, resp.text)
        return False
    except Exception as e:
        app.logger.error('[Email][Mailgun] Exception: %s', e)
        return False


def _send_via_sendgrid(app, sender: str, sender_name: str, to_email: str, subject: str, body: str, *, html: str | None = None, template_id: str | None = None, dynamic_data: dict | None = None) -> bool:
    # Prefer DB-stored key from settings if available
    api_key = app.config.get('SENDGRID_API_KEY', '')
    try:
        from app.models.settings import Settings  # local import to avoid circular at module load
        with app.app_context():
            s = Settings.get_settings()
            if s and s.sendgrid_api_key:
                api_key = s.sendgrid_api_key
    except Exception:
        pass
    if not api_key:
        app.logger.warning('[Email][SendGrid] Not configured.')
        return False
    try:
        payload = {
            'personalizations': [{ 'to': [{ 'email': to_email }] }],
            'from': { 'email': sender, **({'name': sender_name} if sender_name else {}) }
        }
        if template_id:
            payload['template_id'] = template_id
            if dynamic_data:
                payload['personalizations'][0]['dynamic_template_data'] = dynamic_data
        else:
            # non-template content
            contents = []
            if html:
                contents.append({ 'type': 'text/html', 'value': html })
            contents.append({ 'type': 'text/plain', 'value': body or '' })
            payload['subject'] = subject
            payload['content'] = contents
        resp = requests.post(
            'https://api.sendgrid.com/v3/mail/send',
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json=payload, timeout=15
        )
        if resp.status_code in (200, 202):
            return True
        app.logger.error('[Email][SendGrid] Failed status=%s body=%s', resp.status_code, resp.text)
        return False
    except Exception as e:
        app.logger.error('[Email][SendGrid] Exception: %s', e)
        return False


def send_email(app, to_email: str, subject: str, body: str, html: str | None = None, provider_options: dict | None = None) -> bool:
    """Send an email using the configured provider (SMTP default, Mailgun, SendGrid).
    Optional html and provider_options can be provided for provider-specific features (e.g., SendGrid dynamic templates).
    provider_options keys:
      - sendgrid_template_id: str
      - sendgrid_dynamic_data: dict
    """
    sender = app.config.get('MAIL_SENDER', 'no-reply@example.com')
    sender_name = app.config.get('MAIL_SENDER_NAME', '')
    provider = (app.config.get('EMAIL_PROVIDER') or 'SMTP').upper()
    # Prefer provider from DB settings if available
    try:
        from app.models.settings import Settings  # local import to avoid circular
        with app.app_context():
            s = Settings.get_settings()
            if s and s.email_provider:
                provider = (s.email_provider or 'SMTP').upper()
    except Exception:
        pass

    if provider == 'MAILGUN':
        return _send_via_mailgun(app, sender, sender_name, to_email, subject, body)
    if provider == 'SENDGRID':
        provider_options = provider_options or {}
        return _send_via_sendgrid(
            app, sender, sender_name, to_email, subject, body,
            html=html,
            template_id=provider_options.get('sendgrid_template_id'),
            dynamic_data=provider_options.get('sendgrid_dynamic_data')
        )
    # default SMTP
    return _send_via_smtp(app, sender, sender_name, to_email, subject, body)
