from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models.support import SupportTicket
from app import db
from flask_login import login_required, current_user

support_ticket_bp = Blueprint('support_ticket', __name__)

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
