from flask import Blueprint, render_template, request, session, redirect, url_for
from flask_login import login_required, current_user
from app.models.performance import Performance
from app.models.employee import Employee
from app.models.audit import Audit
from app import db

performance_bp = Blueprint('performance', __name__)

@performance_bp.route('/performance', methods=['GET', 'POST'])
@login_required
def performance():
    from datetime import datetime, date
    employees = Employee.query.all()
    if request.method == 'POST':
        # Only allow admins and managers to add evaluations
        if current_user.role not in ('admin', 'manager'):
            return render_template('unauthorized.html')
        employee_id = request.form.get('employee_id')
        review_date_str = request.form.get('review_date') or None
        score = request.form.get('score')
        notes = request.form.get('notes')
        # validate inputs
        try:
            if review_date_str:
                review_date = datetime.strptime(review_date_str, '%Y-%m-%d').date()
            else:
                review_date = date.today()
        except Exception:
            review_date = date.today()
        if employee_id and score:
            try:
                score_int = int(score)
            except Exception:
                score_int = 0
            perf = Performance(employee_id=int(employee_id), review_date=review_date, score=score_int, notes=notes, created_by=current_user.id)
            db.session.add(perf)
            db.session.commit()
            # audit log
            audit = Audit(user_id=current_user.id, action='create', object_type='performance', object_id=perf.id, details=f'score={score_int}')
            db.session.add(audit)
            db.session.commit()
    # prepare display data with employee names
    performance_rows = []
    for p in Performance.query.order_by(Performance.review_date.desc()).all():
        emp = Employee.query.get(p.employee_id)
        performance_rows.append({
            'id': p.id,
            'employee_name': emp.name if emp else '—',
            'review_date': p.review_date,
            'score': p.score,
            'notes': p.notes
        })
    return render_template('performance.html', lang=session.get('lang', 'ar'), employees=employees, performance_data=performance_rows)


@performance_bp.route('/performance/delete/<int:perf_id>', methods=['POST'])
@login_required
def delete_performance(perf_id):
    # Only admin/manager can delete
    if current_user.role not in ('admin', 'manager'):
        return render_template('unauthorized.html')
    p = Performance.query.get(perf_id)
    if not p:
        return ("", 404)
    db.session.delete(p)
    db.session.commit()
    # audit
    audit = Audit(user_id=current_user.id, action='delete', object_type='performance', object_id=perf_id, details='deleted')
    db.session.add(audit)
    db.session.commit()
    return ("", 204)


@performance_bp.route('/performance/edit/<int:perf_id>', methods=['GET', 'POST'])
@login_required
def edit_performance(perf_id):
    # Only admin/manager can edit
    if current_user.role not in ('admin', 'manager'):
        return render_template('unauthorized.html')
    p = Performance.query.get(perf_id)
    if not p:
        return render_template('unauthorized.html')
    employees = Employee.query.all()
    if request.method == 'POST':
        employee_id = request.form.get('employee_id')
        review_date_str = request.form.get('review_date') or None
        score = request.form.get('score')
        notes = request.form.get('notes')
        try:
            if review_date_str:
                review_date = datetime.strptime(review_date_str, '%Y-%m-%d').date()
            else:
                review_date = p.review_date
        except Exception:
            review_date = p.review_date
        try:
            score_int = int(score)
        except Exception:
            score_int = p.score
        p.employee_id = int(employee_id)
        p.review_date = review_date
        p.score = score_int
        p.notes = notes
        db.session.commit()
        # audit
        audit = Audit(user_id=current_user.id, action='update', object_type='performance', object_id=p.id, details=f'score={score_int}')
        db.session.add(audit)
        db.session.commit()
        return redirect(url_for('performance.performance'))
    return render_template('performance_edit.html', perf=p, employees=employees, lang=session.get('lang', 'ar'))
