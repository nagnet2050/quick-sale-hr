from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from app.models.permission import Role, Permission, RolePermission, UserRole, PermissionLog
from app.models.permission import initialize_default_permissions, initialize_default_roles, assign_admin_permissions
from app.models.user import User
from app import db
from app.permissions import has_permission
from datetime import datetime

permissions_bp = Blueprint('permissions', __name__)


@permissions_bp.route('/admin/permissions')
@login_required
def manage_permissions():
    """صفحة إدارة الأدوار والصلاحيات"""
    if not has_permission(['admin']):
        return render_template('unauthorized.html'), 403
    return render_template('manage_roles.html', lang=session.get('lang', 'ar'))


# ==================== Roles API ====================

@permissions_bp.route('/api/roles', methods=['GET'])
@login_required
def get_roles():
    """الحصول على قائمة الأدوار"""
    if not current_user.has_permission(['admin', 'manager']):
        return jsonify({'error': 'Unauthorized'}), 403
    
    roles = Role.query.all()
    result = []
    
    for role in roles:
        result.append({
            'id': role.id,
            'name': role.name,
            'display_name_ar': role.display_name_ar,
            'display_name_en': role.display_name_en,
            'description': role.description,
            'is_active': role.is_active,
            'permissions_count': len(role.permissions),
            'created_at': role.created_at.isoformat() if role.created_at else None
        })
    
    return jsonify(result)


@permissions_bp.route('/api/roles/<int:role_id>', methods=['GET'])
@login_required
def get_role(role_id):
    """الحصول على تفاصيل دور محدد"""
    if not current_user.has_permission(['admin', 'manager']):
        return jsonify({'error': 'Unauthorized'}), 403
    
    role = Role.query.get_or_404(role_id)
    
    return jsonify({
        'id': role.id,
        'name': role.name,
        'display_name_ar': role.display_name_ar,
        'display_name_en': role.display_name_en,
        'description': role.description,
        'is_active': role.is_active,
        'permissions': [rp.permission_id for rp in role.permissions if rp.granted]
    })


@permissions_bp.route('/api/roles', methods=['POST'])
@login_required
def create_role():
    """إنشاء دور جديد"""
    if not has_permission(['admin']):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        data = request.get_json()
        
        # Check if role exists
        if Role.query.filter_by(name=data['name']).first():
            return jsonify({'error': 'Role already exists'}), 400
        
        # Create role
        role = Role(
            name=data['name'],
            display_name_ar=data.get('display_name_ar'),
            display_name_en=data.get('display_name_en'),
            description=data.get('description'),
            is_active=data.get('is_active', True)
        )
        db.session.add(role)
        db.session.flush()
        
        # Assign permissions
        if 'permissions' in data:
            for perm_id in data['permissions']:
                rp = RolePermission(
                    role_id=role.id,
                    permission_id=perm_id,
                    granted=True,
                    granted_by=current_user.id
                )
                db.session.add(rp)
        
        # Log action
        log = PermissionLog(
            action='create_role',
            target_type='role',
            target_id=role.id,
            details=f"Created role: {role.name}",
            performed_by=current_user.id,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        
        db.session.commit()
        
        return jsonify({'success': True, 'id': role.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@permissions_bp.route('/api/roles/<int:role_id>', methods=['PUT'])
@login_required
def update_role(role_id):
    """تحديث دور"""
    if not has_permission(['admin']):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        role = Role.query.get_or_404(role_id)
        data = request.get_json()
        
        # Update basic info
        # Allow changing role name (except for admin) with uniqueness check
        new_name = data.get('name')
        if new_name and new_name != role.name:
            if role.name == 'admin':
                return jsonify({'error': 'Cannot rename admin role'}), 400
            if Role.query.filter(Role.name == new_name, Role.id != role.id).first():
                return jsonify({'error': 'Role name already exists'}), 400
            role.name = new_name
        role.display_name_ar = data.get('display_name_ar', role.display_name_ar)
        role.display_name_en = data.get('display_name_en', role.display_name_en)
        role.description = data.get('description', role.description)
        if 'is_active' in data:
            role.is_active = bool(data.get('is_active'))
        role.updated_at = datetime.utcnow()
        
        # Update permissions
        if 'permissions' in data:
            # Remove old permissions
            RolePermission.query.filter_by(role_id=role.id).delete()
            
            # Add new permissions
            for perm_id in data['permissions']:
                rp = RolePermission(
                    role_id=role.id,
                    permission_id=perm_id,
                    granted=True,
                    granted_by=current_user.id
                )
                db.session.add(rp)
        
        # Log action
        log = PermissionLog(
            action='update_role',
            target_type='role',
            target_id=role.id,
            details=f"Updated role: {role.name}",
            performed_by=current_user.id,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@permissions_bp.route('/api/roles/<int:role_id>', methods=['DELETE'])
@login_required
def delete_role(role_id):
    """حذف دور"""
    if not has_permission(['admin']):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        role = Role.query.get_or_404(role_id)
        
        # Prevent deleting admin role
        if role.name == 'admin':
            return jsonify({'error': 'Cannot delete admin role'}), 400
        
        # Check if role is assigned to users
        if UserRole.query.filter_by(role_id=role.id).count() > 0:
            return jsonify({'error': 'Role is assigned to users. Remove assignments first.'}), 400
        
        # Log action
        log = PermissionLog(
            action='delete_role',
            target_type='role',
            target_id=role.id,
            details=f"Deleted role: {role.name}",
            performed_by=current_user.id,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        
        db.session.delete(role)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== Permissions API ====================

@permissions_bp.route('/api/permissions', methods=['GET'])
@login_required
def get_permissions():
    """الحصول على قائمة الصلاحيات"""
    if not current_user.has_permission(['admin', 'manager']):
        return jsonify({'error': 'Unauthorized'}), 403
    
    permissions = Permission.query.order_by(Permission.module, Permission.action).all()
    
    result = []
    for perm in permissions:
        result.append({
            'id': perm.id,
            'module': perm.module,
            'action': perm.action,
            'display_name_ar': perm.display_name_ar,
            'display_name_en': perm.display_name_en,
            'description': perm.description
        })
    
    return jsonify(result)


# ==================== User Roles API ====================

@permissions_bp.route('/api/user-roles', methods=['GET'])
@login_required
def get_user_roles():
    """الحصول على أدوار المستخدمين مع Pagination & Optimization"""
    if not current_user.has_permission(['admin', 'manager']):
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get pagination & search parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '').strip()
    
    # Build query - simple query without eager loading (since relationship doesn't exist)
    query = User.query.filter_by(active=True)
    
    # Apply search filter
    if search:
        query = query.filter(User.username.contains(search))
    
    # Paginate
    pagination = query.order_by(User.username).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    result = []
    for user in pagination.items:
        # Get user roles manually
        user_roles = UserRole.query.filter_by(user_id=user.id).all()
        
        roles = []
        primary_role = None
        
        for ur in user_roles:
            if ur.role and ur.role.is_active:
                role_data = {
                    'id': ur.role.id,
                    'name': ur.role.name,
                    'name_ar': ur.role.display_name_ar,
                    'name_en': ur.role.display_name_en
                }
                roles.append(role_data)
                
                if ur.is_primary:
                    primary_role = role_data
        
        result.append({
            'user_id': user.id,
            'username': user.username,
            'roles': roles,
            'primary_role': primary_role
        })
    
    return jsonify({
        'user_roles': result,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    })


@permissions_bp.route('/api/user-roles', methods=['POST'])
@login_required
def assign_user_role():
    """تعيين دور لمستخدم"""
    if not has_permission(['admin']):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        data = request.get_json()
        user_id = data['user_id']
        role_id = data['role_id']
        is_primary = data.get('is_primary', False)
        
        # Check if already assigned
        existing = UserRole.query.filter_by(user_id=user_id, role_id=role_id).first()
        if existing:
            return jsonify({'error': 'Role already assigned to this user'}), 400
        
        # If setting as primary, remove primary from other roles
        if is_primary:
            UserRole.query.filter_by(user_id=user_id, is_primary=True).update({'is_primary': False})
        
        # Create assignment
        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            is_primary=is_primary,
            assigned_by=current_user.id
        )
        db.session.add(user_role)
        
        # Log action
        log = PermissionLog(
            action='assign_role',
            target_type='user',
            target_id=user_id,
            details=f"Assigned role {role_id} to user {user_id}",
            performed_by=current_user.id,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@permissions_bp.route('/api/user-roles/<int:user_role_id>', methods=['DELETE'])
@login_required
def remove_user_role(user_role_id):
    """إزالة دور من مستخدم"""
    if not has_permission(['admin']):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        user_role = UserRole.query.get_or_404(user_role_id)
        
        # Log action
        log = PermissionLog(
            action='remove_role',
            target_type='user',
            target_id=user_role.user_id,
            details=f"Removed role {user_role.role_id} from user {user_role.user_id}",
            performed_by=current_user.id,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        
        db.session.delete(user_role)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== Users API ====================

@permissions_bp.route('/api/users', methods=['GET'])
@login_required
def get_users():
    """الحصول على قائمة المستخدمين مع Pagination & Search"""
    if not current_user.has_permission(['admin', 'manager']):
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get pagination & search parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '').strip()
    
    # Build query
    query = User.query.filter_by(active=True)
    
    # Apply search filter
    if search:
        query = query.filter(
            db.or_(
                User.username.contains(search),
                User.email.contains(search)
            )
        )
    
    # Paginate
    pagination = query.order_by(User.username).paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    result = []
    for user in pagination.items:
        result.append({
            'id': user.id,
            'username': user.username,
            'role': user.role
        })
    
    return jsonify({
        'users': result,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    })


# ==================== Initialize Permissions ====================

@permissions_bp.route('/api/permissions/initialize', methods=['POST'])
@login_required
def init_permissions():
    """تهيئة الصلاحيات الافتراضية"""
    if not has_permission(['admin']):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        initialize_default_permissions()
        initialize_default_roles()
        assign_admin_permissions()
        
        return jsonify({'success': True, 'message': 'Permissions initialized successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
