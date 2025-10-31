from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app.models.support import SupportTicket
from app import db
from datetime import datetime

support_bp = Blueprint('support', __name__)

@support_bp.route('/support', methods=['GET', 'POST'])
@login_required
def support():
    if request.method == 'POST':
        client_phone = request.form['client_phone']
        issue = request.form['issue']
        resolved = 'resolved' in request.form
        escalated = 'escalated' in request.form
        time_spent = int(request.form['time_spent'])
        ticket = SupportTicket(
            employee_id=current_user.id,
            client_phone=client_phone,
            issue=issue,
            resolved=resolved,
            escalated=escalated,
            time_spent=time_spent,
            created_at=datetime.now(),
            resolved_at=datetime.now() if resolved else None
        )
        db.session.add(ticket)
        db.session.commit()
        flash('تم تسجيل الدعم بنجاح', 'success')
        return redirect(url_for('support.support'))
    tickets = SupportTicket.query.filter_by(employee_id=current_user.id).all()
    return render_template('support.html', tickets=tickets, lang=session.get('lang', 'ar'))
