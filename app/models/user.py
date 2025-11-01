from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(16), nullable=False)  # 'admin' or 'employee' (للتوافق مع النظام القديم)
    active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, required_roles=None, module=None, action=None):
        """
        فحص ما إذا كان المستخدم لديه الصلاحية المطلوبة
        Args:
            required_roles: قائمة الأدوار المطلوبة (للتوافق مع النظام القديم)
            module: اسم الموديول (employees, payroll, etc.)
            action: نوع العملية (view, create, edit, delete, etc.)
        """
        # المستخدم الرئيسي لديه جميع الصلاحيات
        if self.username == '1' or self.role == 'admin':
            return True
        
        # فحص الصلاحيات الجديدة (module + action)
        if module and action:
            return self.check_permission(module, action)
        
        # فحص الدور العادي (للتوافق مع النظام القديم)
        if required_roles:
            if isinstance(required_roles, str):
                return self.role == required_roles
            elif isinstance(required_roles, (list, tuple)):
                return self.role in required_roles
        
        return False
    
    def check_permission(self, module, action):
        """فحص صلاحية محددة"""
        from app.models.permission import Permission, RolePermission, UserRole
        
        # جلب الأدوار المعينة للمستخدم
        user_roles = UserRole.query.filter_by(user_id=self.id).all()
        
        for user_role in user_roles:
            role = user_role.role
            if not role.is_active:
                continue
            
            # البحث عن الصلاحية
            perm = Permission.query.filter_by(module=module, action=action).first()
            if not perm:
                continue
            
            # فحص إذا كان الدور يمتلك هذه الصلاحية
            role_perm = RolePermission.query.filter_by(
                role_id=role.id,
                permission_id=perm.id,
                granted=True
            ).first()
            
            if role_perm:
                return True
        
        return False
    
    def get_roles(self):
        """الحصول على قائمة الأدوار المعينة"""
        from app.models.permission import UserRole
        
        user_roles = UserRole.query.filter_by(user_id=self.id).all()
        return [ur.role for ur in user_roles if ur.role.is_active]
    
    def get_primary_role(self):
        """الحصول على الدور الأساسي"""
        from app.models.permission import UserRole
        
        user_roles = UserRole.query.filter_by(user_id=self.id).all()
        primary = next((ur.role for ur in user_roles if ur.is_primary and ur.role.is_active), None)
        if primary:
            return primary
        
        # إذا لم يوجد دور أساسي، إرجاع أول دور
        roles = self.get_roles()
        return roles[0] if roles else None
    
    def has_any_permission(self, module, actions):
        """فحص إذا كان المستخدم يمتلك أي من الصلاحيات المطلوبة"""
        for action in actions:
            if self.check_permission(module, action):
                return True
        return False
