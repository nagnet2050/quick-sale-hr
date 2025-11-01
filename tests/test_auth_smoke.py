import os
import pytest

# Ensure in-memory DB for tests
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from app import create_app, db  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.employee import Employee  # noqa: E402

@pytest.fixture(scope='function')
def app_client():
    app = create_app()
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,  # safety; login is exempt but keep minimal friction
        'SERVER_NAME': 'localhost'
    })
    with app.app_context():
        # Fresh DB is created by auto_migrate in create_app for in-memory
        # Create an employee with id 1 and a known password
        emp = Employee(id=1, code='EMP-0001', name='Test Admin Employee', department='support', active=True)
        emp.set_password('Secret123!')
        db.session.add(emp)
        db.session.commit()

        # Ensure an admin user exists with username '1'
        admin = User.query.filter_by(username='1').first()
        if not admin:
            admin = User(username='1', role='admin', active=True)
            # Its password is irrelevant for login now; set a random one
            admin.set_password('irrelevant')
            db.session.add(admin)
            db.session.commit()

    with app.test_client() as client:
        yield client


def test_employee_login_success(app_client):
    # Employee login with correct password should redirect to /dashboard
    resp = app_client.post('/login', data={
        'user_type': 'employee',
        'user_id': '1',
        'password': 'Secret123!'
    }, follow_redirects=False)
    assert resp.status_code in (302, 303), resp.data.decode()
    assert '/dashboard' in resp.headers.get('Location', ''), resp.headers


def test_admin_login_with_employee_password_success(app_client):
    # Find admin user id
    with create_app().app_context():
        admin = User.query.filter_by(username='1').first()
        assert admin is not None
        admin_id = admin.id
    # Admin login should accept the employee's password
    resp = app_client.post('/login', data={
        'user_type': 'admin',
        'user_id': str(admin_id),
        'password': 'Secret123!'
    }, follow_redirects=False)
    assert resp.status_code in (302, 303), resp.data.decode()
    assert '/dashboard' in resp.headers.get('Location', ''), resp.headers


def test_admin_login_wrong_password_rejected(app_client):
    with create_app().app_context():
        admin = User.query.filter_by(username='1').first()
        admin_id = admin.id
    resp = app_client.post('/login', data={
        'user_type': 'admin',
        'user_id': str(admin_id),
        'password': 'WrongPass!'
    }, follow_redirects=True)
    # Should not redirect to dashboard; should show login page with error message
    assert resp.status_code == 200
    body = resp.data.decode('utf-8', errors='ignore')
    assert 'Invalid password' in body or 'كلمة المرور غير صحيحة' in body
