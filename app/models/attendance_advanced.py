"""
نماذج متقدمة للحضور: التقارير والتكامل مع الرواتب
"""
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func

class AttendanceReport(db.Model):
    """تقارير الحضور المجمّعة"""
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    
    # الفترة
    period_type = db.Column(db.String(20))  # 'daily', 'weekly', 'monthly'
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    
    # إحصائيات الحضور
    total_days = db.Column(db.Integer, default=0)  # إجمالي أيام العمل
    present_days = db.Column(db.Integer, default=0)  # أيام الحضور
    absent_days = db.Column(db.Integer, default=0)  # أيام الغياب
    late_days = db.Column(db.Integer, default=0)  # أيام التأخير
    
    # الوقت
    total_work_minutes = db.Column(db.Integer, default=0)  # إجمالي دقائق العمل
    total_late_minutes = db.Column(db.Integer, default=0)  # إجمالي دقائق التأخير
    total_overtime_minutes = db.Column(db.Integer, default=0)  # إجمالي ساعات إضافي
    average_late_minutes = db.Column(db.Float, default=0.0)  # متوسط التأخير
    
    # المخالفات
    location_violations = db.Column(db.Integer, default=0)  # تسجيل من خارج الموقع
    time_violations = db.Column(db.Integer, default=0)  # تسجيل خارج الأوقات
    device_violations = db.Column(db.Integer, default=0)  # أجهزة غير مسجلة
    
    # التكامل مع الرواتب
    linked_to_payroll = db.Column(db.Boolean, default=False)
    payroll_id = db.Column(db.Integer, db.ForeignKey('payroll.id'), nullable=True)
    
    # التدقيق
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    generated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # العلاقات
    employee = db.relationship('Employee', backref='attendance_reports')
    payroll = db.relationship('Payroll', backref='attendance_report', uselist=False)


class AttendanceSync(db.Model):
    """قائمة انتظار المزامنة للوضع Offline"""
    id = db.Column(db.Integer, primary_key=True)
    
    # معلومات السجل
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    action = db.Column(db.String(20))  # 'check_in', 'check_out'
    timestamp = db.Column(db.DateTime, nullable=False)
    
    # الموقع
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    address = db.Column(db.String(256))
    
    # الجهاز
    mac_address = db.Column(db.String(17))
    device_info = db.Column(db.String(256))
    
    # حالة المزامنة
    sync_status = db.Column(db.String(20), default='pending')  # pending, synced, failed
    sync_attempts = db.Column(db.Integer, default=0)
    last_sync_attempt = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    
    # البيانات الأصلية (JSON)
    original_data = db.Column(db.Text)  # JSON string
    
    # التدقيق
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    synced_at = db.Column(db.DateTime)
    
    employee = db.relationship('Employee', backref='sync_queue')


class AttendanceRBAC(db.Model):
    """قواعد RBAC للحضور"""
    id = db.Column(db.Integer, primary_key=True)
    
    # القاعدة
    rule_name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    
    # نوع القاعدة
    rule_type = db.Column(db.String(50))  # 'user', 'role', 'department', 'device', 'location', 'time'
    
    # التطبيق
    applies_to = db.Column(db.Text)  # JSON: user_ids, role_names, departments, etc.
    
    # الأذونات
    can_check_in = db.Column(db.Boolean, default=True)
    can_check_out = db.Column(db.Boolean, default=True)
    can_check_for_others = db.Column(db.Boolean, default=False)
    
    # القيود
    allowed_devices = db.Column(db.Text)  # JSON: list of MAC addresses
    allowed_locations = db.Column(db.Text)  # JSON: list of locations with radius
    allowed_time_ranges = db.Column(db.Text)  # JSON: time ranges
    
    # الحالة
    is_active = db.Column(db.Boolean, default=True)
    priority = db.Column(db.Integer, default=0)  # القاعدة الأعلى أولوية تطبّق أولاً
    
    # التدقيق
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PayrollAttendanceLink(db.Model):
    """ربط الحضور بالرواتب - التحويل التلقائي"""
    id = db.Column(db.Integer, primary_key=True)
    
    payroll_id = db.Column(db.Integer, db.ForeignKey('payroll.id'), nullable=False)
    report_id = db.Column(db.Integer, db.ForeignKey('attendance_report.id'), nullable=False)
    
    # الحسابات التلقائية
    late_deduction_amount = db.Column(db.Float, default=0.0)
    absence_deduction_amount = db.Column(db.Float, default=0.0)
    overtime_bonus_amount = db.Column(db.Float, default=0.0)
    
    # القواعد المستخدمة
    late_deduction_rate = db.Column(db.Float)  # جنيه/دقيقة
    absence_deduction_rate = db.Column(db.Float)  # جنيه/يوم
    overtime_bonus_rate = db.Column(db.Float)  # جنيه/ساعة
    
    # الحالة
    auto_calculated = db.Column(db.Boolean, default=True)
    approved = db.Column(db.Boolean, default=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    approved_at = db.Column(db.DateTime)
    
    # التدقيق
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    payroll = db.relationship('Payroll', backref='attendance_link')
    report = db.relationship('AttendanceReport', backref='payroll_link')
