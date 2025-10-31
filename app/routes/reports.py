from flask import Blueprint, render_template, session
from flask_login import login_required, current_user
from app.models.employee import Employee
from app.models.leave import Leave
from app.models.performance import Performance
from app.models.attendance import Attendance

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/reports')
@login_required
def reports():
    if current_user.role not in ('admin', 'manager', 'executive'):
        return render_template('unauthorized.html')
    total_employees = Employee.query.count()
    pending_leaves = Leave.query.filter_by(status='Pending').count()
    # avg performance score
    perf_rows = Performance.query.all()
    avg_score = None
    if perf_rows:
        avg_score = sum([p.score or 0 for p in perf_rows]) / len(perf_rows)
        avg_score = round(avg_score, 2)
    # recent attendance count
    recent_att = Attendance.query.order_by(Attendance.id.desc()).limit(50).count()
    stats = {
        'total_employees': total_employees,
        'pending_leaves': pending_leaves,
        'avg_score': avg_score,
        'recent_attendance_count': recent_att
    }
    return render_template('reports.html', stats=stats, lang=session.get('lang', 'ar'))
