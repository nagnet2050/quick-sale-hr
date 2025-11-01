from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from app.models.client_support import ClientSupport, ClientTransferHistory
from app.models.user import User
from app import db
from app.permissions import has_permission
from datetime import datetime
from sqlalchemy import or_, and_

client_support_bp = Blueprint('client_support', __name__)

# ============================================================
# نظام تحويل العملاء بين الأقسام
# Client Transfer System Between Departments
# ============================================================
# الأقسام المتاحة: الدعم الفني، المبيعات، الإدارة
# Available Departments: Technical Support, Sales, Management
# ============================================================

# قاموس الأقسام المتاحة للتحويل (الدعم الفني، المبيعات، الإدارة فقط)
DEPARTMENTS = {
    'technical_support': {'name_ar': 'الدعم الفني', 'name_en': 'Technical Support', 'icon': 'fa-headset', 'color': 'info'},
    'sales': {'name_ar': 'المبيعات', 'name_en': 'Sales', 'icon': 'fa-shopping-cart', 'color': 'success'},
    'billing': {'name_ar': 'المحاسبة', 'name_en': 'Billing', 'icon': 'fa-file-invoice-dollar', 'color': 'warning'},
    'management': {'name_ar': 'الإدارة', 'name_en': 'Management', 'icon': 'fa-building', 'color': 'primary'}
}

@client_support_bp.route('/client-support', methods=['GET', 'POST'])
@login_required
def client_support():
    """صفحة دعم العملاء الرئيسية"""
    # توجيه GET إلى الشاشة الموحدة (دعم + متابعة) مع الإبقاء على POST لإنشاء التذاكر
    if request.method == 'GET':
        return redirect(url_for('support_hub.support_hub'))

    if request.method == 'POST':
        try:
            client_phone = request.form['client_phone']
            client_name = request.form['client_name']
            client_email = request.form.get('client_email')
            client_company = request.form.get('client_company')
            issue = request.form['issue']
            issue_type = request.form.get('issue_type', 'general')
            priority = request.form.get('priority', 'medium')
            department = request.form.get('department', 'technical_support')
            
            ticket = ClientSupport(
                client_phone=client_phone,
                client_name=client_name,
                client_email=client_email,
                client_company=client_company,
                issue=issue,
                issue_type=issue_type,
                priority=priority,
                department=department,
                status='new',
                created_by=current_user.id
            )
            db.session.add(ticket)
            db.session.commit()
            
            flash('تم تسجيل التذكرة بنجاح' if session.get('lang') == 'ar' else 'Ticket created successfully', 'success')
            return redirect(url_for('client_support.client_support'))
        except Exception as e:
            db.session.rollback()
            flash(f'خطأ في إنشاء التذكرة: {str(e)}', 'danger')
    
    # فلترة التذاكر
    department_filter = request.args.get('department', 'all')
    status_filter = request.args.get('status', 'all')
    
    query = ClientSupport.query
    
    # فلترة حسب القسم
    if department_filter != 'all':
        query = query.filter_by(department=department_filter)
    
    # فلترة حسب الحالة
    if status_filter == 'open':
        query = query.filter(ClientSupport.resolved == False)
    elif status_filter == 'resolved':
        query = query.filter(ClientSupport.resolved == True)
    elif status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    tickets = query.order_by(ClientSupport.created_at.desc()).all()
    
    # إحصائيات
    stats = {
        'total': ClientSupport.query.count(),
        'open': ClientSupport.query.filter_by(resolved=False).count(),
        'resolved': ClientSupport.query.filter_by(resolved=True).count(),
        'technical': ClientSupport.query.filter_by(department='technical_support').count(),
        'sales': ClientSupport.query.filter_by(department='sales').count(),
        'high_priority': ClientSupport.query.filter_by(priority='high').count(),
        'urgent': ClientSupport.query.filter_by(priority='urgent').count()
    }
    
    return render_template('client_support_new.html', 
                         tickets=tickets, 
                         departments=DEPARTMENTS,
                         stats=stats,
                         lang=session.get('lang', 'ar'))


@client_support_bp.route('/client-support/view/<int:ticket_id>', methods=['GET'])
@login_required
def client_support_view(ticket_id):
    """عرض تفاصيل تذكرة دعم"""
    ticket = ClientSupport.query.get_or_404(ticket_id)
    return render_template(
        'client_support_view.html',
        ticket=ticket,
        departments=DEPARTMENTS,
        lang=session.get('lang', 'ar')
    )

@client_support_bp.route('/client-support/respond/<int:ticket_id>', methods=['POST'])
@login_required
def respond_to_issue(ticket_id):
    """الرد على تذكرة"""
    if not has_permission(['admin', 'manager']):
        flash('غير مصرح لك بالرد', 'danger')
        return redirect(url_for('client_support.client_support'))
    
    ticket = ClientSupport.query.get_or_404(ticket_id)
    
    response = request.form.get('admin_response')
    ticket.admin_response = response
    ticket.status = 'in_progress'
    ticket.updated_at = datetime.utcnow()
    
    db.session.commit()
    flash('تم تسجيل رد الإدارة', 'success')
    return redirect(url_for('client_support.client_support'))


# ==================== API Endpoints للتحويل ====================

@client_support_bp.route('/api/client-support/transfer/<int:ticket_id>', methods=['POST'])
@login_required
def transfer_ticket(ticket_id):
    """تحويل تذكرة بين الأقسام"""
    try:
        data = request.get_json()
        
        ticket = ClientSupport.query.get_or_404(ticket_id)
        
        to_department = data.get('to_department')
        to_user_id = data.get('to_user')
        transfer_reason = data.get('transfer_reason')
        transfer_notes = data.get('transfer_notes')
        
        if not to_department or not transfer_reason:
            return jsonify({'success': False, 'error': 'القسم المستهدف وسبب التحويل مطلوبان'}), 400
        
        if to_department not in DEPARTMENTS:
            return jsonify({'success': False, 'error': 'قسم غير صحيح'}), 400
        
        # حفظ القسم السابق
        from_department = ticket.department
        from_user = ticket.assigned_to
        
        # إنشاء سجل التحويل
        transfer_history = ClientTransferHistory(
            ticket_id=ticket.id,
            from_department=from_department,
            to_department=to_department,
            from_user=from_user,
            to_user=to_user_id,
            transfer_reason=transfer_reason,
            transfer_notes=transfer_notes,
            transferred_by=current_user.id
        )
        
        # تحديث التذكرة
        ticket.department = to_department
        ticket.assigned_to = to_user_id
        ticket.status = 'transferred'
        ticket.transfer_count += 1
        ticket.last_transferred_at = datetime.utcnow()
        ticket.last_transferred_by = current_user.id
        ticket.transfer_reason = transfer_reason
        ticket.updated_at = datetime.utcnow()
        
        db.session.add(transfer_history)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'تم تحويل التذكرة من {DEPARTMENTS[from_department]["name_ar"]} إلى {DEPARTMENTS[to_department]["name_ar"]}',
            'ticket': ticket.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@client_support_bp.route('/api/client-support/transfer-history/<int:ticket_id>', methods=['GET'])
@login_required
def get_transfer_history(ticket_id):
    """الحصول على تاريخ تحويلات التذكرة"""
    try:
        ticket = ClientSupport.query.get_or_404(ticket_id)
        
        transfers = ClientTransferHistory.query.filter_by(ticket_id=ticket_id)\
            .order_by(ClientTransferHistory.created_at.desc()).all()
        
        # إضافة أسماء المستخدمين
        transfers_data = []
        for transfer in transfers:
            transfer_dict = transfer.to_dict()
            
            # اسم من قام بالتحويل
            transferred_by_user = User.query.get(transfer.transferred_by)
            transfer_dict['transferred_by_name'] = transferred_by_user.username if transferred_by_user else 'غير معروف'
            
            # اسم الموظف السابق
            if transfer.from_user:
                from_user = User.query.get(transfer.from_user)
                transfer_dict['from_user_name'] = from_user.username if from_user else 'غير معروف'
            
            # اسم الموظف الجديد
            if transfer.to_user:
                to_user = User.query.get(transfer.to_user)
                transfer_dict['to_user_name'] = to_user.username if to_user else 'غير معروف'
            
            # أسماء الأقسام
            transfer_dict['from_department_name'] = DEPARTMENTS.get(transfer.from_department, {}).get('name_ar', transfer.from_department)
            transfer_dict['to_department_name'] = DEPARTMENTS.get(transfer.to_department, {}).get('name_ar', transfer.to_department)
            
            transfers_data.append(transfer_dict)
        
        return jsonify({
            'success': True,
            'transfers': transfers_data,
            'count': len(transfers_data)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@client_support_bp.route('/api/client-support/assign/<int:ticket_id>', methods=['POST'])
@login_required
def assign_ticket(ticket_id):
    """تعيين تذكرة لموظف"""
    try:
        data = request.get_json()
        
        ticket = ClientSupport.query.get_or_404(ticket_id)
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'error': 'يجب تحديد الموظف'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'الموظف غير موجود'}), 404
        
        ticket.assigned_to = user_id
        ticket.status = 'assigned'
        ticket.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'تم تعيين التذكرة للموظف {user.username}',
            'ticket': ticket.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@client_support_bp.route('/api/client-support/update-status/<int:ticket_id>', methods=['POST'])
@login_required
def update_ticket_status(ticket_id):
    """تحديث حالة التذكرة"""
    try:
        data = request.get_json()
        
        ticket = ClientSupport.query.get_or_404(ticket_id)
        new_status = data.get('status')
        resolution_notes = data.get('resolution_notes')
        
        if not new_status:
            return jsonify({'success': False, 'error': 'يجب تحديد الحالة الجديدة'}), 400
        
        ticket.status = new_status
        
        if new_status == 'resolved' or new_status == 'closed':
            ticket.resolved = True
            ticket.resolved_at = datetime.utcnow()
            if resolution_notes:
                ticket.resolution_notes = resolution_notes
        
        ticket.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم تحديث حالة التذكرة',
            'ticket': ticket.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@client_support_bp.route('/api/client-support/departments/<department>', methods=['GET'])
@login_required
def get_department_users(department):
    """الحصول على موظفي قسم معين"""
    try:
        # يمكن تحسين هذا باستخدام نظام الصلاحيات الجديد
        # لكن حالياً سنعيد جميع المستخدمين النشطين
        users = User.query.filter_by(active=True).all()
        
        users_data = [{'id': u.id, 'username': u.username, 'role': u.role} for u in users]
        
        return jsonify({
            'success': True,
            'users': users_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@client_support_bp.route('/api/client-support/stats', methods=['GET'])
@login_required
def get_support_stats():
    """إحصائيات دعم العملاء"""
    try:
        total = ClientSupport.query.count()
        open_tickets = ClientSupport.query.filter_by(resolved=False).count()
        resolved = ClientSupport.query.filter_by(resolved=True).count()
        
        by_department = {}
        # الأقسام المعروفة مسبقاً
        for dept_key in DEPARTMENTS.keys():
            count = ClientSupport.query.filter_by(department=dept_key).count()
            by_department[dept_key] = {
                'count': count,
                'name': DEPARTMENTS[dept_key]['name_ar']
            }
        # إضافة أي أقسام موجودة في قاعدة البيانات وغير معرّفة في القاموس
        distinct_depts = db.session.query(ClientSupport.department).distinct().all()
        for (dept_val,) in distinct_depts:
            if dept_val and dept_val not in by_department:
                count = ClientSupport.query.filter_by(department=dept_val).count()
                by_department[dept_val] = {
                    'count': count,
                    'name': dept_val
                }
        
        by_status = {}
        statuses = ['new', 'assigned', 'in_progress', 'transferred', 'resolved', 'closed']
        for status in statuses:
            by_status[status] = ClientSupport.query.filter_by(status=status).count()
        
        by_priority = {}
        priorities = ['low', 'medium', 'high', 'urgent']
        for priority in priorities:
            by_priority[priority] = ClientSupport.query.filter_by(priority=priority).count()
        
        # إحصائيات التحويلات
        total_transfers = ClientTransferHistory.query.count()
        
        # أكثر الأقسام تحويلاً منها
        transfers_from = db.session.query(
            ClientTransferHistory.from_department,
            db.func.count(ClientTransferHistory.id)
        ).group_by(ClientTransferHistory.from_department).all()
        
        # أكثر الأقسام تحويلاً إليها
        transfers_to = db.session.query(
            ClientTransferHistory.to_department,
            db.func.count(ClientTransferHistory.id)
        ).group_by(ClientTransferHistory.to_department).all()
        
        return jsonify({
            'success': True,
            'stats': {
                'total': total,
                'open': open_tickets,
                'resolved': resolved,
                'by_department': by_department,
                'by_status': by_status,
                'by_priority': by_priority,
                'total_transfers': total_transfers,
                'transfers_from': [{'department': t[0], 'count': t[1]} for t in transfers_from],
                'transfers_to': [{'department': t[0], 'count': t[1]} for t in transfers_to]
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
