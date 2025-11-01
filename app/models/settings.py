from app import db
from datetime import datetime

class Settings(db.Model):
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # معلومات الشركة - Company Information
    company_name_ar = db.Column(db.String(200))
    company_name_en = db.Column(db.String(200))
    company_logo = db.Column(db.String(500))  # path to logo
    company_email = db.Column(db.String(200))
    company_phone = db.Column(db.String(50))
    company_address_ar = db.Column(db.Text)
    company_address_en = db.Column(db.Text)
    company_website = db.Column(db.String(200))
    tax_number = db.Column(db.String(100))
    commercial_register = db.Column(db.String(100))
    
    # إعدادات الموقع - Location Settings
    company_lat = db.Column(db.Float)
    company_lng = db.Column(db.Float)
    allowed_radius_meters = db.Column(db.Integer, default=500)  # نطاق الحضور المسموح
    
    # أوقات العمل - Work Hours
    work_start = db.Column(db.String(8), default='09:00')
    work_end = db.Column(db.String(8), default='17:00')
    break_start = db.Column(db.String(8))
    break_end = db.Column(db.String(8))
    work_days = db.Column(db.String(100), default='0,1,2,3,4')  # 0=Sunday, 1=Monday...
    weekend_days = db.Column(db.String(50), default='5,6')  # Friday, Saturday
    
    # إعدادات الحضور والانصراف - Attendance Settings
    presence_interval_min = db.Column(db.Integer, default=30)
    presence_grace_min = db.Column(db.Integer, default=5)
    presence_sound_enabled = db.Column(db.Boolean, default=True)
    late_arrival_threshold_min = db.Column(db.Integer, default=15)  # التأخير المسموح
    early_leave_threshold_min = db.Column(db.Integer, default=15)  # المغادرة المبكرة
    auto_checkout_enabled = db.Column(db.Boolean, default=False)  # انصراف تلقائي
    auto_checkout_time = db.Column(db.String(8))  # وقت الانصراف التلقائي
    require_checkout_location = db.Column(db.Boolean, default=True)  # طلب موقع عند الانصراف
    
    # إعدادات الإجازات - Leave Settings
    annual_leave_days = db.Column(db.Integer, default=21)
    sick_leave_days = db.Column(db.Integer, default=30)
    casual_leave_days = db.Column(db.Integer, default=7)
    carry_forward_leaves = db.Column(db.Boolean, default=True)  # ترحيل الإجازات
    max_carry_forward_days = db.Column(db.Integer, default=5)
    leave_approval_required = db.Column(db.Boolean, default=True)
    min_leave_notice_days = db.Column(db.Integer, default=3)  # إشعار مسبق للإجازة
    
    # إعدادات الرواتب - Payroll Settings
    payroll_currency = db.Column(db.String(10), default='SAR')
    payroll_day = db.Column(db.Integer, default=1)  # يوم صرف الراتب من الشهر
    overtime_rate = db.Column(db.Float, default=1.5)  # معدل الساعات الإضافية
    weekend_overtime_rate = db.Column(db.Float, default=2.0)
    holiday_overtime_rate = db.Column(db.Float, default=2.5)
    auto_calculate_overtime = db.Column(db.Boolean, default=True)
    deduct_late_from_salary = db.Column(db.Boolean, default=True)
    late_deduction_rate = db.Column(db.Float, default=0.5)  # معدل خصم التأخير
    
    # إعدادات الإشعارات - Notification Settings
    email_notifications_enabled = db.Column(db.Boolean, default=True)
    sms_notifications_enabled = db.Column(db.Boolean, default=False)
    whatsapp_notifications_enabled = db.Column(db.Boolean, default=True)
    notify_on_late_arrival = db.Column(db.Boolean, default=True)
    notify_on_absence = db.Column(db.Boolean, default=True)
    notify_on_leave_request = db.Column(db.Boolean, default=True)
    notify_managers_on_employee_actions = db.Column(db.Boolean, default=True)
    
    # إعدادات الأمان - Security Settings
    password_min_length = db.Column(db.Integer, default=6)
    password_expiry_days = db.Column(db.Integer, default=90)
    max_login_attempts = db.Column(db.Integer, default=5)
    session_timeout_minutes = db.Column(db.Integer, default=120)
    require_password_change_first_login = db.Column(db.Boolean, default=True)
    two_factor_enabled = db.Column(db.Boolean, default=False)
    
    # إعدادات النظام - System Settings
    language = db.Column(db.String(10), default='ar')
    timezone = db.Column(db.String(50), default='Asia/Riyadh')
    date_format = db.Column(db.String(20), default='DD/MM/YYYY')
    time_format = db.Column(db.String(20), default='HH:mm')
    fiscal_year_start_month = db.Column(db.Integer, default=1)  # يناير
    records_per_page = db.Column(db.Integer, default=25)
    
    # إعدادات التقارير - Reports Settings
    auto_backup_enabled = db.Column(db.Boolean, default=True)
    backup_frequency_days = db.Column(db.Integer, default=7)
    last_backup_date = db.Column(db.DateTime)
    report_logo_enabled = db.Column(db.Boolean, default=True)
    report_footer_text_ar = db.Column(db.Text)
    report_footer_text_en = db.Column(db.Text)
    
    # إعدادات الأداء - Performance Settings
    performance_review_frequency_months = db.Column(db.Integer, default=6)
    min_performance_score = db.Column(db.Float, default=0.0)
    max_performance_score = db.Column(db.Float, default=5.0)
    auto_generate_performance_alerts = db.Column(db.Boolean, default=True)

    # مزود البريد - Email Provider (keys stored securely in DB; used if present)
    email_provider = db.Column(db.String(32))  # SMTP (default) / MAILGUN / SENDGRID
    sendgrid_api_key = db.Column(db.String(256))
    sendgrid_password_changed_template_id = db.Column(db.String(128))
    
    # البيانات الوصفية - Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer)  # user_id
    
    def __repr__(self):
        return f'<Settings {self.company_name_ar or "System"}>'
    
    @staticmethod
    def get_settings():
        """Get or create settings instance"""
        settings = Settings.query.first()
        if not settings:
            settings = Settings()
            db.session.add(settings)
            db.session.commit()
        return settings
