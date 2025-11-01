from flask import Blueprint, render_template, session, abort
from flask_login import login_required, current_user
from app.models.employee import Employee
from app.permissions import has_permission

employee_profile_bp = Blueprint('employee_profile', __name__)

@employee_profile_bp.route('/employee/<int:emp_id>')
@login_required
def employee_profile(emp_id):
    employee = Employee.query.get(emp_id)
    if not employee:
        abort(404)
    # الموظف يرى صفحته فقط، المدير/HR يرى الجميع
    if not has_permission(['admin', 'manager']) and current_user.id != emp_id:
        abort(403)
    return render_template('employee_profile.html', employee=employee, lang=session.get('lang', 'ar'))
