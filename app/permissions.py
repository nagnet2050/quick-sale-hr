"""
نظام فحص الصلاحيات المتقدم
يدعم الصلاحيات القديمة (roles) والجديدة (module + action)
المستخدم برقم 1 لديه جميع الصلاحيات
"""

from functools import wraps
from flask import render_template, current_app
from flask_login import current_user


def require_permission(required_roles=None, module=None, action=None):
    """
    Decorator لفحص صلاحيات المستخدم
    يمكن استخدامه بطريقتين:
    1. @require_permission(['admin', 'manager']) - النظام القديم
    2. @require_permission(module='employees', action='delete') - النظام الجديد
    """
    if isinstance(required_roles, str):
        required_roles = [required_roles]
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # المستخدم الرئيسي (1) لديه جميع الصلاحيات
            if current_user.username == '1' or current_user.role == 'admin':
                return f(*args, **kwargs)
            
            # فحص الصلاحيات الجديدة (module + action)
            if module and action:
                if not current_user.check_permission(module, action):
                    return render_template('unauthorized.html'), 403
            
            # فحص الدور العادي (النظام القديم)
            elif required_roles:
                if current_user.role not in required_roles:
                    return render_template('unauthorized.html'), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def has_permission(required_roles=None, module=None, action=None):
    """
    فحص الصلاحيات بشكل مباشر
    يمكن استخدامه في التعليمات البرمجية العادية
    
    أمثلة:
    - has_permission(['admin', 'manager']) - النظام القديم
    - has_permission(module='payroll', action='delete') - النظام الجديد
    """
    if isinstance(required_roles, str):
        required_roles = [required_roles]
    
    # المستخدم الرئيسي لديه جميع الصلاحيات
    if current_user.username == '1' or current_user.role == 'admin':
        return True
    
    # فحص الصلاحيات الجديدة (module + action)
    if module and action:
        return current_user.check_permission(module, action)
    
    # فحص الدور العادي (النظام القديم)
    if required_roles:
        return current_user.role in required_roles
    
    return False


def check_any_permission(module, actions):
    """
    فحص إذا كان المستخدم يمتلك أي من الصلاحيات المحددة
    مفيد لعرض الأزرار/الخيارات بناءً على صلاحيات متعددة
    
    مثال:
    check_any_permission('employees', ['edit', 'delete'])
    """
    if current_user.username == '1' or current_user.role == 'admin':
        return True
    
    for action in actions:
        if current_user.check_permission(module, action):
            return True
    
    return False


def get_user_permissions(user=None):
    """
    الحصول على قائمة بجميع صلاحيات المستخدم
    مفيد للتحقق من الصلاحيات في الواجهة الأمامية
    """
    if user is None:
        user = current_user
    
    if user.username == '1' or user.role == 'admin':
        return {'all': True}  # جميع الصلاحيات
    
    permissions = {}
    
    for user_role in user.user_roles:
        if not user_role.role.is_active:
            continue
        
        for role_perm in user_role.role.permissions:
            if role_perm.granted:
                perm = role_perm.permission
                module = perm.module
                action = perm.action
                
                if module not in permissions:
                    permissions[module] = []
                
                if action not in permissions[module]:
                    permissions[module].append(action)
    
    return permissions


def can_access_module(module):
    """
    فحص إذا كان المستخدم يمتلك أي صلاحية للوصول إلى موديول معين
    """
    if current_user.username == '1' or current_user.role == 'admin':
        return True
    
    permissions = get_user_permissions()
    
    if permissions.get('all'):
        return True
    
    return module in permissions
