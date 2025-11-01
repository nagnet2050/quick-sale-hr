from flask import Blueprint, render_template, redirect, url_for, flash, session
from flask_login import login_user, login_required
from app.models.user import User
from app import db
from app.models.employee import Employee

employee_login_bp = Blueprint('employee_login', __name__)

@login_required
@employee_login_bp.route('/employee-login', methods=['GET', 'POST'])
def employee_login():
    error = None
    if session.get('user_id'):
        return redirect(url_for('dashboard.dashboard'))
    if session.get('lang') is None:
        session['lang'] = 'ar'
    if session.get('login_attempts') is None:
        session['login_attempts'] = 0
    if session['login_attempts'] > 5:
        error = 'تم تجاوز عدد المحاولات المسموح بها.'
    if error is None and session.get('login_attempts') <= 5:
        if 'POST' == session.get('request_method'):
            username = session.get('form_username')
            password = session.get('form_password')
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                session['user_id'] = user.id
                return redirect(url_for('dashboard.dashboard'))
            else:
                error = 'بيانات الدخول غير صحيحة.'
                session['login_attempts'] += 1
    return render_template('employee_login.html', error=error, lang=session.get('lang', 'ar'))

@employee_login_bp.route('/employee_login', methods=['GET', 'POST'])
def employee_login_post():
    from flask_login import login_user
    from flask import session, flash, redirect, url_for, render_template, request
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        emp = Employee.query.filter_by(name=username).first()
        if emp and emp.check_password(password):
            login_user(emp)
            flash('تم تسجيل الدخول بنجاح', 'success')
            if emp.role == 'manager':
                return redirect(url_for('dashboard.dashboard'))
            else:
                return redirect(url_for('employees.employees'))
        else:
            flash('اسم الموظف أو كلمة المرور غير صحيحة', 'danger')
    return render_template('employee_login.html', lang=session.get('lang', 'ar'))
