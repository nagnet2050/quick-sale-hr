from app import create_app, db
from app.models.user import User
import os, secrets

app = create_app()
with app.app_context():
    # استخدام معرف رقمي يطابق غالباً رقم الموظف المدير
    username = os.environ.get('ADMIN_USERNAME', '1')
    # لا نستخدم كلمة مرور افتراضية ثابتة؛ إما نقرأ من البيئة أو ننشئ كلمة قوية عشوائياً
    provided_pw = os.environ.get('ADMIN_PASSWORD')
    random_pw = secrets.token_urlsafe(16)
    password = provided_pw if provided_pw else random_pw

    existing = User.query.filter_by(username=username).first()
    if not existing:
        admin = User(username=username, role='admin', active=True)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        # لاحظ: الدخول الفعلي يتم بكلمة مرور الموظف المرتبط (تم تطبيقه في auth.login)
        # نطبع كلمة المرور فقط إذا تم توليدها عشوائياً ولم تُمرَّر من البيئة
        if not provided_pw:
            print(f'Admin user created with username: {username} and a random password (not needed for login); keep it safe: {password}')
        else:
            print(f'Admin user created with username: {username} using provided env password.')
    else:
        print('Admin user already exists.')
