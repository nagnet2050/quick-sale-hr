from flask import Blueprint, render_template, request, session
from flask_login import login_required, current_user
from app.models.client_support import ClientSupport
from app.models.user import User
from app.permissions import has_permission
from app.routes.client_support import DEPARTMENTS

support_hub_bp = Blueprint('support_hub', __name__)

@support_hub_bp.route('/support/hub', methods=['GET'])
@login_required
def support_hub():
    """شاشة موحدة لتسجيل الدعم ومتابعة العملاء حسب دور المستخدم"""
    lang = session.get('lang', 'ar')

    # تحديد نوع العرض حسب الصلاحيات
    is_manager = has_permission('admin') or has_permission(module='support', action='manage') or has_permission('view_manager_dashboard')

    # فلاتر اختيارية من الاستعلام
    department_filter = request.args.get('department', 'mine' if not is_manager else 'all')
    status_filter = request.args.get('status', 'open')
    assigned_filter = request.args.get('assigned', 'all')

    # تحضير استعلام تذاكر ClientSupport حسب الدور
    query = ClientSupport.query

    if not is_manager:
        # الموظف يرى تذاكره فقط (المُسندة له أو التي أنشأها)
        query = query.filter(
            (ClientSupport.assigned_to == current_user.id) | (ClientSupport.created_by == current_user.id)
        )
    else:
        # المدير يمكنه رؤية الكل أو التصفية بالقسم إذا تم اختياره
        if department_filter not in (None, '', 'all', 'mine'):
            query = query.filter(ClientSupport.department == department_filter)

    if status_filter == 'open':
        query = query.filter(ClientSupport.resolved == False)
    elif status_filter == 'resolved':
        query = query.filter(ClientSupport.resolved == True)
    elif status_filter not in (None, '', 'all'):
        query = query.filter(ClientSupport.status == status_filter)

    # صلاحيات اختيارية حسب الإعدادات/الصلاحيات
    can_use_assigned_filter = (
        has_permission('admin') or
        has_permission(module='support', action='assigned_filter') or
        has_permission(module='support', action='manage') or
        has_permission('view_manager_dashboard')
    )

    # فلترة المعيّن (فقط لمن يمتلك الصلاحية)
    if can_use_assigned_filter:
        if assigned_filter == 'unassigned':
            query = query.filter(ClientSupport.assigned_to.is_(None))
        else:
            # إذا تم تمرير رقم مستخدم
            try:
                assigned_id = int(assigned_filter)
                if assigned_id > 0:
                    query = query.filter(ClientSupport.assigned_to == assigned_id)
            except (TypeError, ValueError):
                pass

    tickets = query.order_by(ClientSupport.created_at.desc()).limit(200).all()

    # خريطة المستخدمين لعرض أسماء المعيّنين
    user_ids = {t.assigned_to for t in tickets if t.assigned_to} | {t.created_by for t in tickets if t.created_by}
    users_map = {}
    if user_ids:
        users = User.query.filter(User.id.in_(list(user_ids))).all()
        users_map = {u.id: getattr(u, 'username', str(u.id)) for u in users}

    # قائمة كل المستخدمين النشطين لفلتر "المعين إلى"
    users_list = User.query.filter_by(active=True).all() if can_use_assigned_filter else []

    # صلاحية التعيين
    can_assign = (
        has_permission('admin') or
        has_permission(module='support', action='assign') or
        has_permission(module='support', action='manage') or
        has_permission('view_manager_dashboard')
    )

    # تمرير الأعلام والتذاكر للقالب
    return render_template(
        'support_hub.html',
        tickets=tickets,
        is_manager=is_manager,
        lang=lang,
            departments=DEPARTMENTS,
            users_map=users_map,
            users_list=users_list,
            department_filter=department_filter,
            status_filter=status_filter,
            assigned_filter=assigned_filter,
            can_use_assigned_filter=can_use_assigned_filter,
            can_assign=can_assign
    )
