"""Test script to send an email using the app's SMTP configuration.

Usage (PowerShell):
  $env:SMTP_SERVER='smtp.example.com'; $env:SMTP_PORT='587'; $env:SMTP_USERNAME='user@example.com'; $env:SMTP_PASSWORD='password'; $env:MAIL_SENDER='no-reply@example.com'
  python scripts\test_email.py recipient@example.com

This will create the Flask app, load config, and attempt to send a simple test email.
"""
import sys
import logging
from app import create_app


def main():
    if len(sys.argv) < 2:
        print('Usage: python scripts\\test_email.py recipient@example.com')
        return
    recipient = sys.argv[1]

    app = create_app()
    with app.app_context():
        from app.utils.emailer import send_email
        app.logger.setLevel(logging.DEBUG)
        subject = 'Test email from Quick-Sale-HR'
        body = 'This is a test message. If you received this, SMTP is working.'
        ok = send_email(app, recipient, subject, body)
        if ok:
            print(f'[+] Email send attempted to {recipient} — reported as sent')
        else:
            print(f'[-] Email not sent. Check SMTP configuration and application logs for details.')


if __name__ == '__main__':
    main()
