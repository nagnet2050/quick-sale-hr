from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), unique=True, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    address = db.Column(db.String(256))
    job_title = db.Column(db.String(64))
    department = db.Column(db.String(64))
    phone = db.Column(db.String(32))
    email = db.Column(db.String(128))
    active = db.Column(db.Boolean, default=True)
    salary = db.Column(db.Float, default=0.0)
    username = db.Column(db.String(64), unique=True, nullable=True)  # اسم المستخدم (اختياري للموظفين)
    password_hash = db.Column(db.String(128), nullable=True)  # كلمة المرور (اختياري)

    # إضافة العلاقات مع الحذف المتتالي
    attendance_records = db.relationship('Attendance', backref='employee', cascade="all, delete", lazy=True)
    payroll_records = db.relationship('Payroll', backref='employee', cascade="all, delete", lazy=True)
    support_tickets = db.relationship('SupportTicket', backref='employee', cascade="all, delete", lazy=True)

    @property
    def full_name(self):
        """الاسم الكامل للموظف"""
        return self.name

    def set_password(self, password):
        """تعيين كلمة المرور مع التشفير"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """التحقق من كلمة المرور"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
