"""
مسارات الدعم الفني المتقدم
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.support import SupportTicket
from app.models.customer_complaints import CustomerComplaint
from app.models.employee import Employee
from app.permissions import has_permission
from datetime import datetime, timedelta
from sqlalchemy import or_, and_

support_ticket_bp = Blueprint('support_ticket', __name__)


# ==================== المسارات القديمة (للتوافق) ====================

@support_ticket_bp.route('/support-ticket', methods=['GET', 'POST'])
@login_required
def support_ticket():
    if request.method == 'POST':
        phone = request.form.get('customer_phone')
        name = request.form.get('customer_name')
        issue = request.form.get('issue')
        resolved_by_employee = bool(request.form.get('resolved_by_employee'))
        shown_to_management = bool(request.form.get('shown_to_management'))
        resolved_by_management = bool(request.form.get('resolved_by_management'))
        management_response = request.form.get('management_response')
        ticket = SupportTicket(
            customer_phone=phone,
            customer_name=name,
            issue=issue,
            resolved_by_employee=resolved_by_employee,
            shown_to_management=shown_to_management,
            resolved_by_management=resolved_by_management,
            management_response=management_response
        )
        db.session.add(ticket)
        db.session.commit()
        flash('تم حفظ الطلب بنجاح', 'success')
        return redirect(url_for('support_ticket.support_ticket'))
    tickets = SupportTicket.query.order_by(SupportTicket.created_at.desc()).limit(50).all()
    return render_template('support_ticket.html', tickets=tickets, lang=session.get('lang', 'ar'))


# ==================== واجهات المستخدم الجديدة ====================

@support_ticket_bp.route('/support/manager')
@login_required
def manager_support():
    """واجهة المدير لإدارة الشكاوى"""
    if not has_permission('view_manager_dashboard'):
        flash('غير مصرح لك بالوصول', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # جلب قائمة الموظفين للتعيين
    employees = Employee.query.filter_by(active=True).all()
    
    return render_template('manager_support.html', employees=employees)


@support_ticket_bp.route('/support/employee')
@login_required
def employee_support():
    """واجهة الموظف لتنفيذ الحلول"""
    return render_template('employee_support.html')


# ==================== API - المدير ====================

@support_ticket_bp.route('/api/support/manager/complaints')
@login_required
def get_manager_complaints():
    """جلب الشكاوى المحالة للمدير"""
    if not has_permission('view_manager_dashboard'):
        return jsonify({'error': 'غير مصرح'}), 403
    
    # جلب الشكاوى المحالة للمدير الحالي
    complaints = CustomerComplaint.query.filter(
        or_(
            CustomerComplaint.status == 'sent_to_manager',
            CustomerComplaint.status == 'manager_responded',
            CustomerComplaint.status == 'in_progress',
            CustomerComplaint.status == 'resolved'
        ),
        or_(
            CustomerComplaint.referred_to_manager == current_user.id,
            CustomerComplaint.referred_to_manager.is_(None)  # غير محددة
        )
    ).order_by(CustomerComplaint.created_at.desc()).all()
    
    # حساب الإحصائيات
    statistics = {
        'sent_to_manager': sum(1 for c in complaints if c.status == 'sent_to_manager'),
        'in_progress': sum(1 for c in complaints if c.status == 'in_progress'),
        'manager_responded': sum(1 for c in complaints if c.status == 'manager_responded'),
        'resolved': sum(1 for c in complaints if c.status == 'resolved')
    }
    
    return jsonify({
        'complaints': [c.to_dict() for c in complaints],
        'statistics': statistics
    })


@support_ticket_bp.route('/api/support/manager/respond/<int:complaint_id>', methods=['POST'])
@login_required
def manager_respond(complaint_id):
    """رد المدير على الشكوى"""
    if not has_permission('view_manager_dashboard'):
        return jsonify({'error': 'غير مصرح'}), 403
    
    data = request.get_json()
    
    complaint = CustomerComplaint.query.get_or_404(complaint_id)
    
    # تحديث حل المدير
    complaint.manager_solution = data.get('manager_solution')
    complaint.manager_instructions = data.get('manager_instructions')
    complaint.manager_response_date = datetime.utcnow()
    complaint.status = 'manager_responded'
    complaint.referred_to_manager = current_user.id
    
    # تحديث الأولوية إذا تم تغييرها
    if data.get('priority'):
        complaint.priority = data.get('priority')
    
    # تعيين موظف إذا تم اختياره
    if data.get('assigned_to'):
        complaint.assigned_to = data.get('assigned_to')
    
    complaint.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم إرسال الحل بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== API - الموظف ====================

@support_ticket_bp.route('/api/support/employee/tasks')
@login_required
def get_employee_tasks():
    """جلب مهام الموظف"""
    
    # الشكاوى الجديدة (تم الرد من المدير)
    new_tasks = CustomerComplaint.query.filter(
        CustomerComplaint.status == 'manager_responded',
        or_(
            CustomerComplaint.assigned_to == current_user.id,
            CustomerComplaint.assigned_to.is_(None)
        )
    ).order_by(CustomerComplaint.manager_response_date.desc()).all()
    
    # قيد التنفيذ
    progress_tasks = CustomerComplaint.query.filter(
        CustomerComplaint.status == 'in_progress',
        CustomerComplaint.assigned_to == current_user.id
    ).order_by(CustomerComplaint.updated_at.desc()).all()
    
    # المنجزة (آخر 7 أيام)
    week_ago = datetime.utcnow() - timedelta(days=7)
    completed_tasks = CustomerComplaint.query.filter(
        CustomerComplaint.status == 'resolved',
        CustomerComplaint.assigned_to == current_user.id,
        CustomerComplaint.resolved_at >= week_ago
    ).order_by(CustomerComplaint.resolved_at.desc()).all()
    
    return jsonify({
        'new': [t.to_dict() for t in new_tasks],
        'progress': [t.to_dict() for t in progress_tasks],
        'completed': [t.to_dict() for t in completed_tasks]
    })


@support_ticket_bp.route('/api/support/employee/mark-progress/<int:complaint_id>', methods=['POST'])
@login_required
def mark_in_progress(complaint_id):
    """تعليم الشكوى كـ قيد التنفيذ"""
    
    data = request.get_json()
    
    complaint = CustomerComplaint.query.get_or_404(complaint_id)
    
    # تحديث البيانات
    complaint.status = 'in_progress'
    complaint.employee_action = data.get('employee_action')
    complaint.customer_contact_method = data.get('customer_contact_method')
    complaint.customer_response = data.get('customer_response')
    complaint.assigned_to = current_user.id
    complaint.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'تم حفظ التقدم'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@support_ticket_bp.route('/api/support/employee/resolve/<int:complaint_id>', methods=['POST'])
@login_required
def resolve_complaint(complaint_id):
    """تسجيل حل الشكوى"""
    
    data = request.get_json()
    
    complaint = CustomerComplaint.query.get_or_404(complaint_id)
    
    # تحديث البيانات
    complaint.status = 'resolved'
    complaint.employee_action = data.get('employee_action')
    complaint.customer_contact_method = data.get('customer_contact_method')
    complaint.customer_response = data.get('customer_response')
    complaint.resolution_details = data.get('resolution_details')
    complaint.resolved_at = datetime.utcnow()
    complaint.assigned_to = current_user.id
    complaint.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم تسجيل الحل بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== API - عام ====================

@support_ticket_bp.route('/api/support/complaints/<int:complaint_id>')
@login_required
def get_complaint_details(complaint_id):
    """جلب تفاصيل شكوى محددة"""
    
    complaint = CustomerComplaint.query.get_or_404(complaint_id)
    
    return jsonify(complaint.to_dict())


@support_ticket_bp.route('/api/support/assign/<int:complaint_id>', methods=['POST'])
@login_required
def assign_complaint(complaint_id):
    """تحويل الشكوى لمدير أو موظف"""
    
    data = request.get_json()
    
    complaint = CustomerComplaint.query.get_or_404(complaint_id)
    
    # تحديد نوع التحويل
    if data.get('to_manager'):
        complaint.referred_to_manager = data.get('to_manager')
        complaint.status = 'sent_to_manager'
        complaint.referred_to_department = data.get('department', 'Management')
        
    elif data.get('to_employee'):
        complaint.assigned_to = data.get('to_employee')
        complaint.status = 'assigned_to_employee'
    
    complaint.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم التحويل بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

