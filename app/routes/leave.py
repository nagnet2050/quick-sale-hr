from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_required, current_user
from app.models.leave import Leave
from app.models.employee import Employee
from app.models.audit import Audit
from app.models.leave_balance import LeaveBalance
from app import db
from app.permissions import has_permission
from datetime import datetime, timedelta

leave_bp = Blueprint('leave', __name__)


# تعريف أنواع الإجازات (كود → تسمية عربية/مدفوعة؟)
def get_leave_types():
    cfg = current_app.config
    return {
        'annual': {'label_ar': 'سنوية', 'paid': True},
        'weekly': {'label_ar': 'اسبوعية', 'paid': True},
        'holidays': {'label_ar': 'أعياد', 'paid': True},
        'casual': {'label_ar': 'عارضة', 'paid': True},
        'sick': {'label_ar': 'مرضي', 'paid': bool(cfg.get('LEAVE_SICK_IS_PAID', True))},
        'unpaid': {'label_ar': 'غير مدفوعة', 'paid': False},
        'paid': {'label_ar': 'مدفوعة', 'paid': True}
    }


def _days_inclusive(start_date, end_date):
    return (end_date - start_date).days + 1


def _get_or_create_balance(employee_id):
    bal = LeaveBalance.query.filter_by(employee_id=employee_id).first()
    if not bal:
        cfg = current_app.config
        bal = LeaveBalance(
            employee_id=employee_id,
            annual_total=int(cfg.get('LEAVE_ANNUAL_DEFAULT_DAYS', 21)),
            casual_total=int(cfg.get('LEAVE_CASUAL_DEFAULT_DAYS', 6)),
            sick_paid_cap=int(cfg.get('LEAVE_SICK_PAID_DAYS_CAP', 0))
        )
        db.session.add(bal)
        db.session.commit()
    return bal


@leave_bp.route('/leave', methods=['GET', 'POST'])
@login_required
def leave():
    # إرسال طلب إجازة (الموظف)
    if request.method == 'POST':
        leave_type = (request.form.get('leave_type') or '').strip()
        start = request.form.get('start_date')
        end = request.form.get('end_date')
        reason = request.form.get('reason')
        LT = get_leave_types()
        if leave_type not in LT:
            flash('نوع الإجازة غير صالح', 'danger')
            return redirect(url_for('leave.leave'))
        try:
            start_date = datetime.strptime(start, '%Y-%m-%d').date()
            end_date = datetime.strptime(end, '%Y-%m-%d').date()
            if end_date < start_date:
                raise ValueError('end < start')
        except Exception:
            flash('تواريخ غير صالحة', 'danger')
            return redirect(url_for('leave.leave'))
        # تحقق من الرصيد للاسنوية/العارضة
        days = _days_inclusive(start_date, end_date)
        bal = _get_or_create_balance(current_user.id)
        if leave_type == 'annual' and days > bal.annual_available:
            flash('لا يوجد رصيد كافٍ للإجازة السنوية', 'warning')
            return redirect(url_for('leave.leave'))
        if leave_type == 'casual' and days > bal.casual_available:
            flash('لا يوجد رصيد كافٍ للإجازة العارضة', 'warning')
            return redirect(url_for('leave.leave'))

        meta = LT[leave_type]
        l = Leave(
            employee_id=current_user.id,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            paid=bool(meta['paid']),
            reason=reason,
            status='Pending',
            requested_at=datetime.utcnow()
        )
        db.session.add(l)
        db.session.commit()
        audit = Audit(user_id=current_user.id, action='create', object_type='leave', object_id=l.id, details=f"{leave_type} {start}->{end}")
        db.session.add(audit)
        db.session.commit()
        flash('تم إرسال طلب الإجازة', 'success')
        return redirect(url_for('leave.leave'))

    # عرض القائمة: المدير/الأدمن يرون الكل، الموظف يرى طلباته
    if has_permission(['admin', 'manager']):
        records = Leave.query.order_by(Leave.requested_at.desc()).all()
    else:
        records = Leave.query.filter_by(employee_id=current_user.id).order_by(Leave.requested_at.desc()).all()

    rows = []
    for r in records:
        emp = Employee.query.get(r.employee_id)
        label = get_leave_types().get(r.leave_type, {}).get('label_ar', r.leave_type)
        rows.append({
            'id': r.id,
            'employee': emp.name if emp else '—',
            'leave_type': label + (" (مدفوعة)" if r.paid else " (غير مدفوعة)"),
            'start_date': r.start_date,
            'end_date': r.end_date,
            'status': r.status,
            'requested_at': r.requested_at
        })
    # رصيد الموظف الحالي (إن كان موظفاً عادياً)
    bal = None
    if not has_permission(['admin', 'manager']):
        bal = _get_or_create_balance(current_user.id)
    return render_template('leave.html', leaves=rows, lang=session.get('lang', 'ar'), leave_types=get_leave_types(), balance=bal)


@leave_bp.route('/leave/approve/<int:leave_id>', methods=['POST'])
@login_required
def approve_leave(leave_id):
    if not has_permission(['admin', 'manager']):
        return render_template('unauthorized.html')
    l = Leave.query.get(leave_id)
    if not l:
        return ('', 404)
    l.status = 'Approved'
    l.approved_by = current_user.id
    l.approved_at = datetime.utcnow()
    try:
        days = _days_inclusive(l.start_date, l.end_date)
        bal = _get_or_create_balance(l.employee_id)
        # خصم الرصيد عند الإعتماد
        if l.leave_type == 'annual':
            bal.annual_used = int(bal.annual_used or 0) + int(days)
        elif l.leave_type == 'casual':
            bal.casual_used = int(bal.casual_used or 0) + int(days)
        elif l.leave_type == 'sick':
            cap = int(bal.sick_paid_cap or 0)
            if cap <= 0:
                # غير محدود → كل الأيام مدفوعة
                l.paid = True
                l.paid_days = int(days)
            else:
                remaining = max(0, cap - int(bal.sick_used_paid or 0))
                paid_days = min(int(days), int(remaining))
                unpaid_days = int(days) - paid_days
                l.paid_days = paid_days
                # إذا كل المدة مدفوعة → paid=True، وإلا يظل paid=True لكن سنعتمد paid_days في الرواتب
                l.paid = paid_days > 0
                bal.sick_used_paid = int(bal.sick_used_paid or 0) + paid_days
        db.session.add(bal)
    except Exception as _:
        pass
    db.session.commit()
    audit = Audit(user_id=current_user.id, action='update', object_type='leave', object_id=leave_id, details='approved')
    db.session.add(audit)
    db.session.commit()
    return redirect(url_for('leave.leave'))


@leave_bp.route('/leave/reject/<int:leave_id>', methods=['POST'])
@login_required
def reject_leave(leave_id):
    if not has_permission(['admin', 'manager']):
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
