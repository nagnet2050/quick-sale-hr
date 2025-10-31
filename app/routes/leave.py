from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app.models.leave import Leave
from app.models.employee import Employee
from app.models.audit import Audit
from app import db
from datetime import datetime

leave_bp = Blueprint('leave', __name__)


@leave_bp.route('/leave', methods=['GET', 'POST'])
@login_required
def leave():
    # Employees can submit leave; managers/admins can approve
    if request.method == 'POST':
        leave_type = request.form.get('leave_type')
        start = request.form.get('start_date')
        end = request.form.get('end_date')
        try:
            start_date = datetime.strptime(start, '%Y-%m-%d').date()
            end_date = datetime.strptime(end, '%Y-%m-%d').date()
        except Exception:
            flash('Invalid dates', 'danger')
            return redirect(url_for('leave.leave'))
        l = Leave(employee_id=current_user.id, leave_type=leave_type, start_date=start_date, end_date=end_date, status='Pending', requested_at=datetime.utcnow())
        db.session.add(l)
        db.session.commit()
        audit = Audit(user_id=current_user.id, action='create', object_type='leave', object_id=l.id, details=f'{leave_type} {start}->{end}')
        db.session.add(audit)
        db.session.commit()
        flash('Leave request submitted', 'success')
        return redirect(url_for('leave.leave'))

    # Display list: admin/managers see all, employees see their own
    if current_user.role in ('admin', 'manager'):
        records = Leave.query.order_by(Leave.requested_at.desc()).all()
    else:
        records = Leave.query.filter_by(employee_id=current_user.id).order_by(Leave.requested_at.desc()).all()
    # enrich with employee name
    rows = []
    for r in records:
        emp = Employee.query.get(r.employee_id)
        rows.append({
            'id': r.id,
            'employee': emp.name if emp else '—',
            'leave_type': r.leave_type,
            'start_date': r.start_date,
            'end_date': r.end_date,
            'status': r.status,
            'requested_at': r.requested_at
        })
    return render_template('leave.html', leaves=rows, lang=session.get('lang', 'ar'))


@leave_bp.route('/leave/approve/<int:leave_id>', methods=['POST'])
@login_required
def approve_leave(leave_id):
    if current_user.role not in ('admin', 'manager'):
        return render_template('unauthorized.html')
    l = Leave.query.get(leave_id)
    if not l:
        return ('', 404)
    l.status = 'Approved'
    l.approved_by = current_user.id
    l.approved_at = datetime.utcnow()
    db.session.commit()
    audit = Audit(user_id=current_user.id, action='update', object_type='leave', object_id=leave_id, details='approved')
    db.session.add(audit)
    db.session.commit()
    return redirect(url_for('leave.leave'))


@leave_bp.route('/leave/reject/<int:leave_id>', methods=['POST'])
@login_required
def reject_leave(leave_id):
    if current_user.role not in ('admin', 'manager'):
        return render_template('unauthorized.html')
    l = Leave.query.get(leave_id)
    if not l:
        return ('', 404)
    l.status = 'Rejected'
    l.approved_by = current_user.id
    l.approved_at = datetime.utcnow()
    db.session.commit()
    audit = Audit(user_id=current_user.id, action='update', object_type='leave', object_id=leave_id, details='rejected')
    db.session.add(audit)
    db.session.commit()
    return redirect(url_for('leave.leave'))
from flask import Blueprint, render_template, request, session
from flask_login import login_required, current_user
from app.models.leave import Leave
from app.models.employee import Employee
from app import db

leave_bp = Blueprint('leave', __name__)

@leave_bp.route('/leave', methods=['GET', 'POST'])
@login_required
def leave():
    # TODO: Leave management logic
    return render_template('leave.html', lang=session.get('lang', 'ar'))
