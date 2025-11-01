from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from app.models.employee import Employee
from app import db, csrf
from app.permissions import has_permission
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, BooleanField, SelectField, EmailField
from app.constants import REGISTRATION_DEPARTMENTS
from wtforms.validators import DataRequired, Optional

employees_bp = Blueprint('employees', __name__)


class EmployeeForm(FlaskForm):
    code = StringField('الكود', validators=[DataRequired()])
    name = StringField('الاسم', validators=[DataRequired()])
    job_title = StringField('المسمى الوظيفي', validators=[Optional()])
    department = SelectField('القسم', choices=[], validators=[Optional()])
    phone = StringField('الهاتف', validators=[Optional()])
    email = EmailField('البريد الإلكتروني', validators=[Optional()])
    salary = StringField('الراتب', validators=[Optional()])
    active = SelectField('الحالة', choices=[('1', 'نشط'), ('0', 'غير نشط')], default='1')


@employees_bp.route('/employees/edit/<int:emp_id>', methods=['GET', 'POST'])
@login_required
def edit_employee(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    form = EmployeeForm(obj=emp)
    # إعداد قائمة الأقسام مترجمة حسب اللغة
    lang = session.get('lang', 'ar')
    form.department.choices = [(d['key'], d['name_ar'] if lang == 'ar' else d['name_en']) for d in REGISTRATION_DEPARTMENTS]
    if request.method == 'GET' and emp.department:
        form.department.data = emp.department
    if form.validate_on_submit():
        emp.code = form.code.data
        emp.name = form.name.data
        emp.job_title = form.job_title.data
        emp.department = form.department.data
        emp.phone = form.phone.data
        emp.email = form.email.data
        emp.active = bool(int(form.active.data))
        emp.salary = float(form.salary.data) if form.salary.data else 0.0
        db.session.commit()
        flash('تم تعديل بيانات الموظف بنجاح', 'success')
        return redirect(url_for('employees.employees'))
    return render_template('edit_employee.html', form=form, emp=emp, lang=session.get('lang', 'ar'))

@employees_bp.route('/employees/delete/<int:emp_id>', methods=['POST'])
@login_required
def delete_employee(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    db.session.delete(emp)
    db.session.commit()
    flash('تم حذف الموظف بنجاح', 'success')
    return redirect(url_for('employees.employees'))


@employees_bp.route('/employees', methods=['GET', 'POST'])
@login_required
def employees():
    if not has_permission(['admin', 'manager']):
        flash('غير مصرح لك بالدخول', 'danger')
        return redirect(url_for('dashboard.dashboard'))
    form = EmployeeForm()
    # إعداد قائمة الأقسام مترجمة حسب اللغة
    lang = session.get('lang', 'ar')
    form.department.choices = [(d['key'], d['name_ar'] if lang == 'ar' else d['name_en']) for d in REGISTRATION_DEPARTMENTS]
    if form.validate_on_submit():
        # إنشاء username تلقائياً من الكود أو الاسم
        username = form.code.data  # استخدام كود الموظف كـ username
        
        emp = Employee(
            code=form.code.data,
            name=form.name.data,
            job_title=form.job_title.data,
            department=form.department.data,
            phone=form.phone.data,
            email=form.email.data,
            active=bool(int(form.active.data)),
            salary=float(form.salary.data) if form.salary.data else 0.0,
            username=username,
            password_hash=None  # يمكن تعيينها لاحقاً
        )
        db.session.add(emp)
        db.session.commit()
        flash('تمت إضافة الموظف بنجاح', 'success')
        return redirect(url_for('employees.employees'))
    
    # استرجاع جميع الموظفين
    employees = Employee.query.all()
    return render_template('employees.html', employees=employees, lang=session.get('lang', 'ar'), form=form)


# ==================== Password Management Routes ====================

@employees_bp.route('/employees/passwords')
@login_required
def manage_passwords():
    """صفحة إدارة كلمات مرور الموظفين"""
    if not has_permission(['admin', 'manager']):
        flash('غير مصرح لك بالدخول', 'danger')
        return redirect(url_for('dashboard.dashboard'))
    return render_template('employee_passwords.html', lang=session.get('lang', 'ar'))


@employees_bp.route('/api/employees', methods=['GET'])
@csrf.exempt
@login_required
def get_employees_api():
    """API للحصول على قائمة الموظفين مع حالة كلمة المرور"""
    if not has_permission(['admin', 'manager']):
        return jsonify({'error': 'Unauthorized'}), 403
    
    employees = Employee.query.all()
    result = []
    
    for emp in employees:
        result.append({
            'id': emp.id,
            'code': emp.code,
            'name': emp.name,
            'department': emp.department,
            'job_title': emp.job_title,
            'phone': emp.phone,
            'email': emp.email,
            'active': emp.active,
            'has_password': emp.password_hash is not None
        })
    
    return jsonify(result)


@employees_bp.route('/api/employee/<int:emp_id>/password', methods=['PUT'])
@csrf.exempt
@login_required
def set_employee_password(emp_id):
    """تعيين أو تغيير كلمة مرور موظف"""
    if not has_permission(['admin', 'manager']):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        emp = Employee.query.get_or_404(emp_id)
        data = request.get_json()
        password = data.get('password')
        
        if not password or len(password) < 4:
            return jsonify({'error': 'Password must be at least 4 characters'}), 400
        
        emp.set_password(password)
        # مزامنة كلمة المرور مع حساب المدير إن كان اسم المستخدم للمدير هو رقم الموظف
        from app.models.user import User
        admin_user = User.query.filter_by(username=str(emp.id)).first()
        if admin_user:
            admin_user.set_password(password)
        # تحديث حساب الموظف المؤقت إن وجد
        temp_user = User.query.filter_by(username=f'emp_{emp.id}').first()
        if temp_user:
            temp_user.set_password(password)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Password updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@employees_bp.route('/api/employee/<int:emp_id>/password', methods=['DELETE'])
@csrf.exempt
@login_required
def remove_employee_password(emp_id):
    """حذف كلمة مرور موظف"""
    if not has_permission(['admin']):  # Admin only
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        emp = Employee.query.get_or_404(emp_id)
        emp.password_hash = None
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Password removed successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
