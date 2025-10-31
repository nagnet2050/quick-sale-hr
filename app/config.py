import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///hrcloud.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
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
    # Future modules placeholders
    FACE_RECOGNITION_ENABLED = False
    OFFLINE_MODE_ENABLED = False
    PAYROLL_ENABLED = False
    # Payroll defaults (percentages are decimals, e.g., 0.10 == 10%)
    PAYROLL_TAX_RATE = float(os.environ.get('PAYROLL_TAX_RATE', 0.10))
    PAYROLL_INSURANCE_RATE = float(os.environ.get('PAYROLL_INSURANCE_RATE', 0.02))
    PAYROLL_OVERTIME_RATE = float(os.environ.get('PAYROLL_OVERTIME_RATE', 1.5))
    # A simple monthly tax-exempt threshold (amount below which no tax applied)
    PAYROLL_TAX_EXEMPT_LIMIT = float(os.environ.get('PAYROLL_TAX_EXEMPT_LIMIT', 0.0))
