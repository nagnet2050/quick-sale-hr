from app import db
from datetime import datetime

class Role(db.Model):
    """نموذج الأدوار"""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)  # admin, manager, hr, accountant, employee
    display_name_ar = db.Column(db.String(128))  # مدير النظام
    display_name_en = db.Column(db.String(128))  # System Administrator
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    permissions = db.relationship('RolePermission', backref='role', cascade='all, delete-orphan', lazy=True)
    users = db.relationship('UserRole', backref='role', cascade='all, delete-orphan', lazy=True)
    
    def __repr__(self):
        return f'<Role {self.name}>'


class Permission(db.Model):
    """نموذج الصلاحيات"""
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    module = db.Column(db.String(64), nullable=False)  # employees, attendance, payroll, etc.
    action = db.Column(db.String(32), nullable=False)  # view, create, edit, delete, approve, export
    display_name_ar = db.Column(db.String(128))
    display_name_en = db.Column(db.String(128))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # العلاقات
    role_permissions = db.relationship('RolePermission', backref='permission', cascade='all, delete-orphan', lazy=True)
    
    __table_args__ = (
        db.UniqueConstraint('module', 'action', name='unique_module_action'),
    )
    
    def __repr__(self):
        return f'<Permission {self.module}.{self.action}>'


class RolePermission(db.Model):
    """ربط الأدوار بالصلاحيات"""
    __tablename__ = 'role_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'), nullable=False)
    granted = db.Column(db.Boolean, default=True)
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    granted_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    __table_args__ = (
        db.UniqueConstraint('role_id', 'permission_id', name='unique_role_permission'),
    )
    
    def __repr__(self):
        return f'<RolePermission role_id={self.role_id} permission_id={self.permission_id}>'


class UserRole(db.Model):
    """ربط المستخدمين بالأدوار"""
    __tablename__ = 'user_roles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    assigned_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_primary = db.Column(db.Boolean, default=False)  # الدور الأساسي
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'role_id', name='unique_user_role'),
    )
    
    def __repr__(self):
        return f'<UserRole user_id={self.user_id} role_id={self.role_id}>'


class PermissionLog(db.Model):
    """سجل تغييرات الصلاحيات"""
    __tablename__ = 'permission_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(64))  # grant, revoke, modify
    target_type = db.Column(db.String(32))  # role, user, permission
    target_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    performed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    ip_address = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PermissionLog {self.action} on {self.target_type}>'


# =============== Helper Functions ===============

def initialize_default_permissions():
    """إنشاء الصلاحيات الافتراضية"""
    from app import db
    
    modules = [
        # الموظفين
        ('employees', 'view', 'عرض الموظفين', 'View Employees'),
        ('employees', 'create', 'إضافة موظف', 'Create Employee'),
        ('employees', 'edit', 'تعديل موظف', 'Edit Employee'),
        ('employees', 'delete', 'حذف موظف', 'Delete Employee'),
        ('employees', 'export', 'تصدير الموظفين', 'Export Employees'),
        
        # الحضور والانصراف
        ('attendance', 'view', 'عرض الحضور', 'View Attendance'),
        ('attendance', 'create', 'تسجيل حضور', 'Record Attendance'),
        ('attendance', 'edit', 'تعديل الحضور', 'Edit Attendance'),
        ('attendance', 'delete', 'حذف الحضور', 'Delete Attendance'),
        ('attendance', 'export', 'تصدير الحضور', 'Export Attendance'),
        ('attendance', 'approve', 'اعتماد الحضور', 'Approve Attendance'),
        
        # الرواتب
        ('payroll', 'view', 'عرض الرواتب', 'View Payroll'),
        ('payroll', 'create', 'إنشاء راتب', 'Create Payroll'),
        ('payroll', 'edit', 'تعديل راتب', 'Edit Payroll'),
        ('payroll', 'delete', 'حذف راتب', 'Delete Payroll'),
        ('payroll', 'approve', 'اعتماد الرواتب', 'Approve Payroll'),
        ('payroll', 'pay', 'صرف الرواتب', 'Pay Payroll'),
        ('payroll', 'export', 'تصدير الرواتب', 'Export Payroll'),
        
        # الإجازات
        ('leave', 'view', 'عرض الإجازات', 'View Leave'),
        ('leave', 'create', 'طلب إجازة', 'Request Leave'),
        ('leave', 'edit', 'تعديل إجازة', 'Edit Leave'),
        ('leave', 'delete', 'حذف إجازة', 'Delete Leave'),
        ('leave', 'approve', 'اعتماد الإجازات', 'Approve Leave'),
        ('leave', 'export', 'تصدير الإجازات', 'Export Leave'),
        
        # تقييم الأداء
        ('performance', 'view', 'عرض التقييمات', 'View Performance'),
        ('performance', 'create', 'إنشاء تقييم', 'Create Performance'),
        ('performance', 'edit', 'تعديل تقييم', 'Edit Performance'),
        ('performance', 'delete', 'حذف تقييم', 'Delete Performance'),
        ('performance', 'export', 'تصدير التقييمات', 'Export Performance'),
        
        # التقارير
        ('reports', 'view', 'عرض التقارير', 'View Reports'),
        ('reports', 'export', 'تصدير التقارير', 'Export Reports'),
        ('reports', 'financial', 'التقارير المالية', 'Financial Reports'),
        ('reports', 'analytics', 'التحليلات', 'Analytics'),
        
        # الدعم الفني
    ('support', 'view', 'عرض الدعم', 'View Support'),
    ('support', 'create', 'إنشاء تذكرة', 'Create Ticket'),
    ('support', 'edit', 'تعديل تذكرة', 'Edit Ticket'),
    ('support', 'delete', 'حذف تذكرة', 'Delete Ticket'),
    ('support', 'assign', 'تعيين مهام', 'Assign Tasks'),
    # صلاحيات إضافية لإدارة مركز الدعم وفلتر المعيّن
    ('support', 'manage', 'إدارة الدعم', 'Manage Support'),
    ('support', 'assigned_filter', 'استخدام فلتر المعين', 'Use Assigned Filter'),
        
        # الإعدادات
        ('settings', 'view', 'عرض الإعدادات', 'View Settings'),
        ('settings', 'edit', 'تعديل الإعدادات', 'Edit Settings'),
        
        # المستخدمين والصلاحيات
        ('users', 'view', 'عرض المستخدمين', 'View Users'),
        ('users', 'create', 'إضافة مستخدم', 'Create User'),
        ('users', 'edit', 'تعديل مستخدم', 'Edit User'),
        ('users', 'delete', 'حذف مستخدم', 'Delete User'),
        ('users', 'permissions', 'إدارة الصلاحيات', 'Manage Permissions'),
        
        # سجل التدقيق
        ('audit', 'view', 'عرض سجل التدقيق', 'View Audit Log'),
        ('audit', 'export', 'تصدير السجلات', 'Export Logs'),
    ]
    
    for module, action, name_ar, name_en in modules:
        perm = Permission.query.filter_by(module=module, action=action).first()
        if not perm:
            perm = Permission(
                module=module,
                action=action,
                display_name_ar=name_ar,
                display_name_en=name_en
            )
            db.session.add(perm)
    
    db.session.commit()
    print(f"✅ تم إنشاء {len(modules)} صلاحية")


def initialize_default_roles():
    """إنشاء الأدوار الافتراضية"""
    from app import db
    
    roles_data = [
        ('admin', 'مدير النظام', 'System Administrator', 'صلاحيات كاملة على جميع الأنظمة'),
        ('manager', 'مدير', 'Manager', 'إدارة الموظفين والعمليات اليومية'),
        ('hr', 'موارد بشرية', 'HR Manager', 'إدارة الموظفين والرواتب والإجازات'),
        ('accountant', 'محاسب', 'Accountant', 'إدارة الرواتب والتقارير المالية'),
        ('supervisor', 'مشرف', 'Supervisor', 'متابعة الحضور والأداء'),
        ('employee', 'موظف', 'Employee', 'عرض البيانات الشخصية فقط'),
    ]
    
    for name, name_ar, name_en, desc in roles_data:
        role = Role.query.filter_by(name=name).first()
        if not role:
            role = Role(
                name=name,
                display_name_ar=name_ar,
                display_name_en=name_en,
                description=desc
            )
            db.session.add(role)
    
    db.session.commit()
    print(f"✅ تم إنشاء {len(roles_data)} دور")


def assign_admin_permissions():
    """تعيين جميع الصلاحيات للمدير"""
    from app import db
    
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        return
    
    permissions = Permission.query.all()
    for perm in permissions:
        rp = RolePermission.query.filter_by(role_id=admin_role.id, permission_id=perm.id).first()
        if not rp:
            rp = RolePermission(role_id=admin_role.id, permission_id=perm.id, granted=True)
            db.session.add(rp)
    
    db.session.commit()
    print(f"✅ تم تعيين {len(permissions)} صلاحية للمدير")
