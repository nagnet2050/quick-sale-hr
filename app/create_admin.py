from app import create_app, db
from app.models.user import User

app = create_app()
with app.app_context():
    username = 'admin'
    password = 'admin'
    # تحقق من عدم وجود مستخدم بنفس الاسم مسبقًا
    if not User.query.filter_by(username=username).first():
        admin = User(username=username, role='admin', active=True)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print('Admin user created with username: admin and password: admin')
    else:
        print('Admin user already exists.')
