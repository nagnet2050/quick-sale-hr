from flask import Blueprint, render_template, redirect, url_for, flash, session, request, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app.models.employee import Employee
from app import db, login_manager, csrf
from app.forms import LoginForm
from werkzeug.security import check_password_hash
from app.models.audit import Audit
from app.models.password_reset import PasswordResetCode
from datetime import datetime, timedelta
from app.utils.emailer import send_email
from sqlalchemy import func
from app.constants import REGISTRATION_DEPARTMENTS

auth_bp = Blueprint('auth', __name__)

# مجموعة الأقسام المسموح بها (مشتقة من الثوابت المركزية)
ALLOWED_REG_DEPARTMENT_KEYS = {d['key'] for d in REGISTRATION_DEPARTMENTS}

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth_bp.route('/login', methods=['GET', 'POST'])
@csrf.exempt  # Exempt login from CSRF protection temporarily
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        user_type = request.form.get('user_type')
        password = request.form.get('password')
        
        if user_id and user_type and password:
            user = None
            remember = bool(request.form.get('remember'))
            
            if user_type == 'admin':
                # تسجيل دخول مدير باستخدام كلمة مرور الموظف المرتبط (إلغاء أي كلمة مرور افتراضية)
                user = User.query.get(int(user_id))
                if user:
                    # حدد الموظف المرتبط بحسب اسم المستخدم الرقمي أو نفس المعرّف
                    emp_id = None
                    try:
                        if isinstance(user.username, str) and user.username.isdigit():
                            emp_id = int(user.username)
                    except Exception:
                        emp_id = None

                    employee = Employee.query.get(emp_id) if emp_id else None
                    if employee and employee.password_hash and employee.check_password(password):
                        # نجاح: الدخول بحساب المدير، لكن عبر كلمة مرور الموظف
                        login_user(user, remember=remember)
                        # تخزين تعريف الموظف في الجلسة للاستخدام داخل النظام
                        session['employee_id'] = employee.id
                        session['employee_name'] = employee.full_name
                        flash('تم تسجيل الدخول بنجاح' if session.get('lang', 'ar') == 'ar' else 'Login successful', 'success')
                        return redirect(url_for('dashboard.dashboard'))
                    elif employee and not employee.password_hash:
                        flash('لم يتم تعيين كلمة مرور لهذا الموظف' if session.get('lang', 'ar') == 'ar' else 'No password set for this employee', 'warning')
                    else:
                        flash('كلمة المرور غير صحيحة' if session.get('lang', 'ar') == 'ar' else 'Invalid password', 'danger')
                else:
                    flash('مستخدم غير موجود' if session.get('lang', 'ar') == 'ar' else 'User not found', 'danger')
                    
            elif user_type == 'employee':
                # تسجيل دخول موظف من جدول Employee
                employee = Employee.query.get(int(user_id))
                if employee and employee.password_hash and employee.check_password(password):
                    # إنشاء كائن user مؤقت للموظف
                    temp_user = User.query.filter_by(username=f'emp_{employee.id}').first()
                    if not temp_user:
                        # إنشاء user مؤقت إذا لم يكن موجود
                        temp_user = User(
                            username=f'emp_{employee.id}',
                            role='employee'
                        )
                        temp_user.password_hash = employee.password_hash
                        db.session.add(temp_user)
                        db.session.commit()
                    
                    login_user(temp_user, remember=remember)
                    # حفظ معلومات الموظف في الجلسة
                    session['employee_id'] = employee.id
                    session['employee_name'] = employee.full_name
                    flash('تم تسجيل الدخول بنجاح' if session.get('lang', 'ar') == 'ar' else 'Login successful', 'success')
                    return redirect(url_for('dashboard.dashboard'))
                elif employee and not employee.password_hash:
                    flash('لم يتم تعيين كلمة مرور لهذا الموظف' if session.get('lang', 'ar') == 'ar' else 'No password set for this employee', 'warning')
                    
            if not user:
                flash('كلمة المرور غير صحيحة' if session.get('lang', 'ar') == 'ar' else 'Invalid password', 'danger')
        else:
            flash('يرجى اختيار مستخدم وإدخال كلمة المرور' if session.get('lang', 'ar') == 'ar' else 'Please select user and enter password', 'warning')

    # جلب قائمة المديرين والموظفين
    # جلب المديرين فقط (مستخدمين بدور manager أو admin وليسوا موظفين)
    admins = User.query.filter(
        User.active == True,
        User.role.in_(['admin', 'manager']),
        ~User.username.like('emp_%')  # استبعاد حسابات الموظفين المؤقتة
    ).all()
    
    # جلب الموظفين النشطين الذين لديهم كلمة مرور
    employees = Employee.query.filter(
        Employee.active == True,
        Employee.password_hash.isnot(None)
    ).all()

    # إخفاء الموظف الذي لديه حساب مدير (مثلاً الموظف رقم 1) من قائمة الموظفين
    # أي مستخدم إداري username له رقم يدل على Employee.id سيتم استبعاده من قائمة الموظفين
    try:
        admin_employee_ids = set()
        for admin in admins:
            if isinstance(admin.username, str) and admin.username.isdigit():
                admin_employee_ids.add(int(admin.username))
        if admin_employee_ids:
            employees = [e for e in employees if e.id not in admin_employee_ids]
    except Exception:
        # تجاهل أي أخطاء غير متوقعة في عملية التصفية
        pass
    
    # ربط كل مدير بموظف إن وجد
    for admin in admins:
        try:
            # محاولة الحصول على معلومات الموظف من user_id
            employee = Employee.query.get(int(admin.username)) if admin.username.isdigit() else None
            if employee:
                admin.display_name = f"{employee.full_name or employee.name} - مدير"
            else:
                admin.display_name = f"{admin.username} - مدير"
        except:
            admin.display_name = f"{admin.username} - مدير"
    
    form = LoginForm()
    return render_template('login.html', form=form, lang=session.get('lang', 'ar'), admins=admins, employees=employees, reg_departments=REGISTRATION_DEPARTMENTS)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/employee/register', methods=['POST'])
@csrf.exempt
def employee_register():
    """تسجيل موظف لأول مرة من شاشة الدخول.
    يولّد كود موظف تلقائياً، ويتحقق إن كان مسجلاً مسبقاً عبر الهاتف أو البريد.
    لا يُنشئ كلمة مرور؛ يمكنه ضبطها لاحقاً من (نسيت كلمة المرور) باستخدام البريد.
    """
    try:
        data = request.get_json() if request.is_json else request.form
        name = (data.get('name') or '').strip()
        address = (data.get('address') or '').strip()
        phone = (data.get('phone') or '').strip()
        job_title = (data.get('job_title') or '').strip()
        department = (data.get('department') or '').strip()
        email = (data.get('email') or '').strip()

        # التحقق من الحقول الأساسية
        if not name:
            return jsonify({'success': False, 'message': 'الاسم مطلوب'}), 400
        if not phone and not email:
            return jsonify({'success': False, 'message': 'رقم الهاتف أو البريد الإلكتروني مطلوب'}), 400
        if not department:
            return jsonify({'success': False, 'message': 'القسم مطلوب'}), 400
        if department not in ALLOWED_REG_DEPARTMENT_KEYS:
            return jsonify({'success': False, 'message': 'قسم غير صالح'}), 400

        # تحقق إذا كان مسجلاً مسبقاً
        exists_q = Employee.query
        if phone:
            exists_q = exists_q.filter((Employee.phone == phone) | (Employee.email == email) if email else (Employee.phone == phone))
        elif email:
            exists_q = exists_q.filter(Employee.email == email)
        existing = exists_q.first()
        if existing:
            return jsonify({'success': False, 'message': 'هذا الموظف مسجل من قبل', 'employee': {'id': existing.id, 'code': existing.code, 'name': existing.name}}), 409

        # توليد كود تلقائي بناءً على أعلى معرّف
        next_id = (db.session.query(func.max(Employee.id)).scalar() or 0) + 1
        code = f"EMP-{next_id:04d}"

        emp = Employee(
            code=code,
            name=name,
            address=address or None,
            job_title=job_title or None,
            department=department,
            phone=phone or None,
            email=email or None,
            active=True
        )
        db.session.add(emp)
        db.session.commit()

        return jsonify({'success': True, 'message': 'تم تسجيل الموظف بنجاح', 'employee': {'id': emp.id, 'code': emp.code, 'name': emp.name}})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@auth_bp.route('/forgot-password', methods=['POST'])
@csrf.exempt
def forgot_password():
    """استقبال طلب إعادة تعيين كلمة المرور (تسجيله فقط لإشعار الأدمن)."""
    try:
        user_type = request.form.get('user_type') or (request.get_json() or {}).get('user_type')
        user_id = request.form.get('user_id') or (request.get_json() or {}).get('user_id')
        contact = request.form.get('contact') or (request.get_json() or {}).get('contact')

        # تطبيع القيم
        user_type = (user_type or '').strip()
        user_id = int(user_id) if user_id else None
        contact = (contact or '').strip()

        # تحقق مبسط من المدخلات
        if not user_type or not user_id:
            return {'success': False, 'message': 'بيانات غير مكتملة'}, 400

        # التثبت من وجود الحساب (اختياري)
        exists = False
        if user_type == 'admin':
            exists = bool(User.query.get(user_id))
        elif user_type == 'employee':
            exists = bool(Employee.query.get(user_id))

        # سجل تدقيق ليتابع الأدمن الطلب
        audit = Audit(
            user_id=None,
            action='password_reset_request',
            object_type=user_type,
            object_id=user_id,
            details=f'contact={contact or "-"}; exists={exists}; ip={request.remote_addr}'
        )
        db.session.add(audit)
        db.session.commit()

        # لا نفصح عن وجود/عدم وجود الحساب
        return {'success': True, 'message': 'تم استلام طلب إعادة التعيين وسيتم مراجعته.'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': str(e)}, 500


@auth_bp.route('/forgot-password/request', methods=['POST'])
@csrf.exempt
def forgot_password_request():
    """إرسال كود إعادة التعيين إلى البريد المسجل للموظف (لا نفصح عن وجود الحساب)."""
    try:
        email = (request.form.get('email') or (request.get_json() or {}).get('email') or '').strip()
        if not email:
            return jsonify({'success': False, 'message': 'Email required'}), 400

        # ابحث عن الموظف بواسطة البريد
        employee = Employee.query.filter(Employee.email.isnot(None), Employee.email == email).first()

        # بغض النظر، نرجع نجاح لمنع تسريب وجود/عدم وجود البريد
        if not employee:
            return jsonify({'success': True})

        # تحقق من التبريد (cooldown)
        cooldown = current_app.config.get('PASSWORD_RESET_RESEND_COOLDOWN_SEC', 60)
        ttl = current_app.config.get('PASSWORD_RESET_CODE_TTL_MIN', 10)
        latest = PasswordResetCode.query.filter_by(employee_id=employee.id, email=email).order_by(PasswordResetCode.created_at.desc()).first()
        now = datetime.utcnow()
        if latest and (now - latest.created_at).total_seconds() < cooldown:
            reset = latest
        else:
            # أنشئ كود مؤقت جديد
            reset = PasswordResetCode.generate(employee.id, email, ttl_minutes=ttl)
            db.session.commit()

        # أرسل الكود عبر البريد (إذا لم يتم تهيئة SMTP سيتم تسجيله فقط في الـ logs)
        company = current_app.config.get('COMPANY_NAME', 'Quick Sale HR')
        subject = f"{company} - رمز إعادة تعيين كلمة المرور"
        body = f"مرحباً {employee.name},\n\nرمز التحقق الخاص بك هو: {reset.code}\nصلاحيته {ttl} دقائق.\n\n{company}"
        sent = send_email(current_app, email, subject, body)
        # سجل تدقيق
        audit = Audit(
            user_id=None,
            action='password_reset_code_sent',
            object_type='employee',
            object_id=employee.id,
            details=f'email={email}; sent={sent}; ip={request.remote_addr}'
        )
        db.session.add(audit)
        db.session.commit()
        resp = {'success': True}
        # خيار تطويري: إرجاع الكود في الاستجابة للبيئات المحلية فقط
        if current_app.config.get('DEV_ALLOW_CODE_IN_RESPONSE'):
            resp['debug_code'] = reset.code
        return jsonify(resp)
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@auth_bp.route('/forgot-password/verify', methods=['POST'])
@csrf.exempt
def forgot_password_verify():
    """التحقق من الكود وتعيين كلمة مرور جديدة للموظف وربط حساب المدير إن وجد."""
    try:
        data = request.get_json() if request.is_json else request.form
        email = (data.get('email') or '').strip()
        code = (data.get('code') or '').strip()
        new_password = (data.get('new_password') or '').strip()

        if not email or not code or not new_password:
            return jsonify({'success': False, 'message': 'Missing fields'}), 400
        if len(new_password) < 4:
            return jsonify({'success': False, 'message': 'Password too short'}), 400

        employee = Employee.query.filter(Employee.email == email).first()
        if not employee:
            # لا نفصح
            return jsonify({'success': False, 'message': 'Invalid code'}), 400

        # ابحث عن آخر كود غير مستخدم ولن ينتهي بعد
        reset = PasswordResetCode.query.filter_by(employee_id=employee.id, email=email, used=False).order_by(PasswordResetCode.created_at.desc()).first()
        if not reset:
            return jsonify({'success': False, 'message': 'Invalid code'}), 400

        # تحقق من الصلاحية والكود
        now = datetime.utcnow()
        if reset.expires_at < now:
            return jsonify({'success': False, 'message': 'Code expired'}), 400
        # تحقق من عدد المحاولات
        max_attempts = current_app.config.get('PASSWORD_RESET_MAX_ATTEMPTS', 5)
        if (reset.attempts or 0) >= max_attempts:
            reset.used = True
            db.session.commit()
            return jsonify({'success': False, 'message': 'Too many attempts. Request a new code.'}), 400
        if reset.code != code:
            reset.attempts = (reset.attempts or 0) + 1
            db.session.commit()
            return jsonify({'success': False, 'message': 'Invalid code'}), 400

        # نجاح: حدّث كلمة مرور الموظف
        employee.set_password(new_password)

        # مزامنة كلمة مرور المدير إذا كان هناك مستخدم admin بنفس رقم الموظف كاسم مستخدم
        admin_user = User.query.filter_by(username=str(employee.id)).first()
        if admin_user:
            admin_user.set_password(new_password)

        # تحديث حساب temp للموظف إن وجد (emp_{id})
        temp_user = User.query.filter_by(username=f'emp_{employee.id}').first()
        if temp_user:
            temp_user.set_password(new_password)

        reset.used = True

        # سجل تدقيق
        audit = Audit(
            user_id=None,
            action='password_reset_completed',
            object_type='employee',
            object_id=employee.id,
            details=f'email={email}; ip={request.remote_addr}'
        )
        db.session.add(audit)
        db.session.commit()
        # إشعار عبر البريد: تم تغيير كلمة المرور
        try:
            company = current_app.config.get('COMPANY_NAME', 'Quick Sale HR')
            support_email = current_app.config.get('SUPPORT_EMAIL', 'support@example.com')
            change_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
            subject = f"{company} - تم تغيير كلمة المرور"
            body = (
                f"مرحباً {employee.name},\n\n"
                f"تم تغيير كلمة المرور الخاصة بحسابك في {company} بتاريخ {change_time}.\n"
                f"إذا لم تكن أنت من قام بذلك، يُرجى التواصل فوراً مع الدعم: {support_email}.\n\n"
                f"{company}"
            )
            # Determine provider (DB settings has priority)
            provider = (current_app.config.get('EMAIL_PROVIDER') or 'SMTP').upper()
            try:
                from app.models.settings import Settings
                s = Settings.get_settings()
                if s and s.email_provider:
                    provider = (s.email_provider or 'SMTP').upper()
            except Exception:
                pass
            provider_options = None
            if provider == 'SENDGRID':
                tpl = None
                try:
                    from app.models.settings import Settings
                    s = Settings.get_settings()
                    if s and s.sendgrid_password_changed_template_id:
                        tpl = s.sendgrid_password_changed_template_id
                except Exception:
                    tpl = None
                # fallback to config
                if not tpl:
                    tpl = current_app.config.get('SENDGRID_PASSWORD_CHANGED_TEMPLATE_ID')
                if tpl:
                    provider_options = {
                        'sendgrid_template_id': tpl,
                        'sendgrid_dynamic_data': {
                            'name': employee.name,
                            'change_time': change_time,
                            'support_email': support_email
                        }
                    }
            # أرسل الإشعار (لا يؤثر على نتيجة الطلب)
            send_email(current_app, employee.email, subject, body, provider_options=provider_options)
        except Exception as _e:
            current_app.logger.warning('Password-changed email notify failed: %s', _e)
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
