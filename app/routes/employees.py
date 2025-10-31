from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app.models.employee import Employee
from app import db

employees_bp = Blueprint('employees', __name__)

@employees_bp.route('/employees', methods=['GET', 'POST'])
@login_required
def employees():
    if current_user.role != 'admin':
        flash('غير مصرح لك بالدخول', 'danger')
        return redirect(url_for('dashboard.dashboard'))
    if request.method == 'POST':
        code = request.form.get('code')
        name = request.form.get('name')
        job_title = request.form.get('job_title')
        department = request.form.get('department')
        phone = request.form.get('phone')
        email = request.form.get('email')
        active = bool(int(request.form.get('active', 1)))
        if code and name:
            emp = Employee(code=code, name=name, job_title=job_title, department=department, phone=phone, email=email, active=active)
            db.session.add(emp)
            db.session.commit()
            flash('تمت إضافة الموظف بنجاح', 'success')
        else:
            flash('يرجى إدخال الكود والاسم', 'danger')
    employees = Employee.query.all()
    return render_template('employees.html', employees=employees, lang=session.get('lang', 'ar'))
