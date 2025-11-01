"""
سكريبت تهيئة نظام الصلاحيات
يقوم بإنشاء الصلاحيات والأدوار الافتراضية
"""

from app import create_app, db
from app.models.permission import (
    Role, Permission, RolePermission, UserRole,
    initialize_default_permissions,
    initialize_default_roles,
    assign_admin_permissions
)
from app.models.user import User

def init_permissions_system():
    """تهيئة نظام الصلاحيات بالكامل"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("تهيئة نظام الصلاحيات المتقدم")
        print("=" * 60)
        
        # 1. إنشاء الصلاحيات الافتراضية
        print("\n[1/4] إنشاء الصلاحيات الافتراضية...")
        initialize_default_permissions()
        
        # 2. إنشاء الأدوار الافتراضية
        print("\n[2/4] إنشاء الأدوار الافتراضية...")
        initialize_default_roles()
        
        # 3. تعيين جميع الصلاحيات للمدير
        print("\n[3/4] تعيين الصلاحيات للمدير...")
        assign_admin_permissions()
        
        # 4. تعيين دور admin للمستخدم الرئيسي
        print("\n[4/4] تعيين الأدوار للمستخدمين...")
        admin_user = User.query.filter_by(username='1').first()
        if admin_user:
            admin_role = Role.query.filter_by(name='admin').first()
            if admin_role:
                # حذف الأدوار القديمة
                UserRole.query.filter_by(user_id=admin_user.id).delete()
                
                # إضافة دور admin
                user_role = UserRole(
                    user_id=admin_user.id,
                    role_id=admin_role.id,
                    is_primary=True
                )
                db.session.add(user_role)
                db.session.commit()
                print(f"✅ تم تعيين دور admin للمستخدم {admin_user.username}")
        
        print("\n" + "=" * 60)
        print("✅ تمت تهيئة النظام بنجاح!")
        print("=" * 60)
        
        # عرض الإحصائيات
        print("\n📊 الإحصائيات:")
        print(f"   - عدد الصلاحيات: {Permission.query.count()}")
        print(f"   - عدد الأدوار: {Role.query.count()}")
        print(f"   - عدد المستخدمين بأدوار: {UserRole.query.count()}")
        
        # عرض الأدوار
        print("\n📋 الأدوار المتاحة:")
        roles = Role.query.all()
        for role in roles:
            perms_count = RolePermission.query.filter_by(role_id=role.id, granted=True).count()
            print(f"   - {role.name}: {role.display_name_ar} ({perms_count} صلاحية)")

if __name__ == '__main__':
    init_permissions_system()
