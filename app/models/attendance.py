from app import db
from datetime import datetime

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
    check_in_time = db.Column(db.DateTime)
    check_out_time = db.Column(db.DateTime)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    address = db.Column(db.String(256))
    lat_out = db.Column(db.Float)
    lng_out = db.Column(db.Float)
    address_out = db.Column(db.String(256))
    status = db.Column(db.String(32))  # 'inside' or 'outside'
    date = db.Column(db.Date)
    
    # معلومات الجهاز والتحقق
    mac_address = db.Column(db.String(17))  # MAC address للجهاز
    device_info = db.Column(db.String(256))  # معلومات إضافية عن الجهاز
    location_verified = db.Column(db.Boolean, default=False)  # هل الموقع داخل النطاق المسموح؟
    time_verified = db.Column(db.Boolean, default=False)  # هل الوقت ضمن ساعات العمل؟
    device_verified = db.Column(db.Boolean, default=False)  # هل الجهاز مسجل؟
    verification_notes = db.Column(db.Text)  # ملاحظات التحقق


class AttendanceSettings(db.Model):
    """إعدادات نظام الحضور والانصراف"""
    id = db.Column(db.Integer, primary_key=True)
    
    # إعدادات الموقع
    company_lat = db.Column(db.Float, default=30.0444)  # موقع الشركة - القاهرة افتراضياً
    company_lng = db.Column(db.Float, default=31.2357)
    max_distance_meters = db.Column(db.Integer, default=100)  # المسافة المسموحة بالمتر
    
    # إعدادات الوقت
    check_in_start = db.Column(db.Time, default=datetime.strptime('07:00', '%H:%M').time())  # بداية وقت الحضور
    check_in_end = db.Column(db.Time, default=datetime.strptime('10:00', '%H:%M').time())  # نهاية وقت الحضور
    check_out_start = db.Column(db.Time, default=datetime.strptime('14:00', '%H:%M').time())  # بداية وقت الانصراف
    check_out_end = db.Column(db.Time, default=datetime.strptime('18:00', '%H:%M').time())  # نهاية وقت الانصراف
    
    # إعدادات التحقق
    require_location_verification = db.Column(db.Boolean, default=True)
    require_time_verification = db.Column(db.Boolean, default=True)
    require_device_verification = db.Column(db.Boolean, default=False)
    allow_outside_hours = db.Column(db.Boolean, default=False)  # السماح بالتسجيل خارج الأوقات
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RegisteredDevice(db.Model):
    """الأجهزة المسجلة للموظفين"""
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    mac_address = db.Column(db.String(17), nullable=False, unique=True)
    device_name = db.Column(db.String(128))  # اسم الجهاز
    device_info = db.Column(db.String(256))  # معلومات الجهاز (نوع المتصفح، OS)
    is_active = db.Column(db.Boolean, default=True)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime)
    
    # علاقة مع الموظف
    employee = db.relationship('Employee', backref='registered_devices')

