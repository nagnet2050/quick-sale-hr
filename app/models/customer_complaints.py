from app import db
from datetime import datetime

class CustomerComplaint(db.Model):
    __tablename__ = 'customer_complaints'
    id = db.Column(db.Integer, primary_key=True)
    customer_phone = db.Column(db.String(20), nullable=False)
    customer_name = db.Column(db.String(100))
    issue_description = db.Column(db.Text, nullable=False)
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # حالات الشكوى: new, assigned_to_employee, sent_to_manager, manager_responded, in_progress, resolved, closed
    status = db.Column(db.String(50), default='new')
    
    # معلومات التحويل والتعيين
    assigned_to = db.Column(db.Integer)  # الموظف المسؤول
    referred_to_manager = db.Column(db.Integer)  # المدير المحال له
    referred_to_department = db.Column(db.String(100))  # الإدارة المحالة لها
    
    # حل المدير
    manager_solution = db.Column(db.Text)  # حل المدير للمشكلة
    manager_response_date = db.Column(db.DateTime)  # تاريخ رد المدير
    manager_instructions = db.Column(db.Text)  # تعليمات المدير للموظف
    
    # تنفيذ الموظف
    employee_action = db.Column(db.Text)  # ما قام به الموظف
    customer_contact_method = db.Column(db.String(50))  # طريقة التواصل: phone, whatsapp, email, visit
    customer_response = db.Column(db.Text)  # رد العميل
    resolution_details = db.Column(db.Text)  # تفاصيل الحل النهائي
    resolved_at = db.Column(db.DateTime)  # تاريخ الحل
    
    # تتبع العمليات
    management_response = db.Column(db.Text)  # رد الإدارة (للتوافق مع الكود القديم)
    response_date = db.Column(db.DateTime)
    resolution_notes = db.Column(db.Text)  # ملاحظات إضافية
    
    # المتابعة
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    category = db.Column(db.String(100))  # تصنيف المشكلة: billing, technical, support, other
    
    # البيانات الأساسية
    created_by = db.Column(db.Integer)  # مسؤول الـ HR اللي أدخل الشكوى
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<CustomerComplaint {self.id} - {self.customer_phone} - {self.status}>'
    
    def to_dict(self):
        """تحويل الشكوى إلى قاموس"""
        return {
            'id': self.id,
            'customer_phone': self.customer_phone,
            'customer_name': self.customer_name,
            'issue_description': self.issue_description,
            'status': self.status,
            'priority': self.priority,
            'category': self.category,
            'assigned_to': self.assigned_to,
            'referred_to_manager': self.referred_to_manager,
            'manager_solution': self.manager_solution,
            'employee_action': self.employee_action,
            'resolution_details': self.resolution_details,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }
