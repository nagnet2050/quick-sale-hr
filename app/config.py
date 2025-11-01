import os

def _normalize_db_uri(uri: str) -> str:
    """Normalize DATABASE_URL for SQLAlchemy.
    Render/Heroku may provide 'postgres://', while SQLAlchemy prefers 'postgresql://'.
    """
    if uri and uri.startswith('postgres://'):
        return uri.replace('postgres://', 'postgresql://', 1)
    return uri

def _engine_options_for(uri: str):
    """Return safe SQLAlchemy engine options based on DB driver.
    Avoid passing SQLite-specific connect_args to other drivers (e.g., psycopg2).
    """
    base = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }
    if uri.startswith('sqlite'):
        base['connect_args'] = {
            'check_same_thread': False,
            'timeout': 30,
        }
    return base

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production-12345678'
    _RAW_DB_URL = os.environ.get('DATABASE_URL', 'sqlite:///hrcloud.db')
    SQLALCHEMY_DATABASE_URI = _normalize_db_uri(_RAW_DB_URL)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = _engine_options_for(SQLALCHEMY_DATABASE_URI)
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    WTF_CSRF_CHECK_DEFAULT = False  # Don't check CSRF on all requests by default
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    LANGUAGES = ['ar', 'en']
    COMPANY_LAT = 24.7136  # Default Riyadh
    COMPANY_LNG = 46.6753
    WORK_START = '08:00'
    WORK_END = '17:00'
    PRESENCE_INTERVAL_MIN = 30
    PRESENCE_GRACE_MIN = 5
    PRESENCE_SOUND_ENABLED = True
    THEME_COLOR = '#0D6EFD'
    FONT_AR = 'Cairo'
    FONT_EN = 'Open Sans'
    LOGO_PATH = '/static/img/logo.png'
    # Email provider configuration
    # Supported providers: SMTP (default), MAILGUN, SENDGRID
    EMAIL_PROVIDER = os.environ.get('EMAIL_PROVIDER', 'SMTP').upper()
    # SMTP settings (generic - works with most providers)
    SMTP_SERVER = os.environ.get('SMTP_SERVER', '')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
    SMTP_USE_TLS = os.environ.get('SMTP_USE_TLS', '1') == '1'
    SMTP_USE_SSL = os.environ.get('SMTP_USE_SSL', '0') == '1'
    MAIL_SENDER = os.environ.get('MAIL_SENDER', 'no-reply@example.com')
    MAIL_SENDER_NAME = os.environ.get('MAIL_SENDER_NAME', 'Quick Sale HR')
    COMPANY_NAME = os.environ.get('COMPANY_NAME', 'Quick Sale HR Cloud')
    SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL', 'support@example.com')
    # Mailgun API settings (optional)
    MAILGUN_DOMAIN = os.environ.get('MAILGUN_DOMAIN', '')
    MAILGUN_API_KEY = os.environ.get('MAILGUN_API_KEY', '')
    # SendGrid API settings (optional)
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', '')
    # Optional: dynamic template for password changed notification
    SENDGRID_PASSWORD_CHANGED_TEMPLATE_ID = os.environ.get('SENDGRID_PASSWORD_CHANGED_TEMPLATE_ID', '')
    # Password reset security knobs
    PASSWORD_RESET_CODE_TTL_MIN = int(os.environ.get('PASSWORD_RESET_CODE_TTL_MIN', 10))
    PASSWORD_RESET_MAX_ATTEMPTS = int(os.environ.get('PASSWORD_RESET_MAX_ATTEMPTS', 5))
    PASSWORD_RESET_RESEND_COOLDOWN_SEC = int(os.environ.get('PASSWORD_RESET_RESEND_COOLDOWN_SEC', 60))
    DEV_ALLOW_CODE_IN_RESPONSE = os.environ.get('DEV_ALLOW_CODE_IN_RESPONSE', '0') == '1'
    # Future modules placeholders
    FACE_RECOGNITION_ENABLED = False
    OFFLINE_MODE_ENABLED = False
    PAYROLL_ENABLED = False
    # Payroll defaults (percentages are decimals, e.g., 0.10 == 10%)
    PAYROLL_TAX_RATE = float(os.environ.get('PAYROLL_TAX_RATE', 0.10))
    PAYROLL_INSURANCE_RATE = float(os.environ.get('PAYROLL_INSURANCE_RATE', 0.02))
    PAYROLL_HEALTH_INSURANCE_RATE = float(os.environ.get('PAYROLL_HEALTH_INSURANCE_RATE', 0.0))
    PAYROLL_OVERTIME_RATE = float(os.environ.get('PAYROLL_OVERTIME_RATE', 1.5))
    PAYROLL_TAX_EXEMPT_LIMIT = float(os.environ.get('PAYROLL_TAX_EXEMPT_LIMIT', 0.0))
    PAYROLL_ABSENCE_DEDUCTION_RATE = float(os.environ.get('PAYROLL_ABSENCE_DEDUCTION_RATE', 1.0))  # خصم يوم كامل
    PAYROLL_LATE_DEDUCTION_PER_HOUR = float(os.environ.get('PAYROLL_LATE_DEDUCTION_PER_HOUR', 0.0))  # خصم بالساعة
    # قسط السلف/القروض تلقائياً ضمن الراتب
    PAYROLL_AUTO_LOAN_DEDUCTION = os.environ.get('PAYROLL_AUTO_LOAN_DEDUCTION', '1') == '1'
    # Leave defaults and policy
    LEAVE_ANNUAL_DEFAULT_DAYS = int(os.environ.get('LEAVE_ANNUAL_DEFAULT_DAYS', 21))
    LEAVE_CASUAL_DEFAULT_DAYS = int(os.environ.get('LEAVE_CASUAL_DEFAULT_DAYS', 6))
    LEAVE_ALLOW_CARRYOVER = os.environ.get('LEAVE_ALLOW_CARRYOVER', '0') == '1'
    LEAVE_SICK_IS_PAID = os.environ.get('LEAVE_SICK_IS_PAID', '1') == '1'
    # سقف الأيام المدفوعة للمرضي (0 = غير مفعّل/غير محدود)
    LEAVE_SICK_PAID_DAYS_CAP = int(os.environ.get('LEAVE_SICK_PAID_DAYS_CAP', 0))
    LEAVE_WEEKLY_IS_PAID = True
    LEAVE_HOLIDAYS_IS_PAID = True
    # WhatsApp Business API settings
    WHATSAPP_ACCESS_TOKEN = os.environ.get('WHATSAPP_ACCESS_TOKEN', '')
    WHATSAPP_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID', '')
    WHATSAPP_VERIFY_TOKEN = os.environ.get('WHATSAPP_VERIFY_TOKEN', 'your_verify_token')
