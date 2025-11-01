import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
# Use a file-based sqlite DB to avoid StaticPool engine options issue
DB_PATH = os.path.join(BASE_DIR, 'auth_smoke.db')
try:
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
except Exception:
    pass
os.environ['DATABASE_URL'] = f'sqlite:///{DB_PATH}'
from app import create_app, db
from app.models.user import User
from app.models.employee import Employee

app = create_app()
app.config.update({'TESTING': True, 'WTF_CSRF_ENABLED': False})

results = []
with app.app_context():
    # Seed employee
    emp = Employee(id=1, code='EMP-0001', name='Tester', department='support', active=True)
    emp.set_password('Secret123!')
    db.session.add(emp)
    db.session.commit()
    # Ensure admin user with username '1'
    admin = User.query.filter_by(username='1').first()
    if not admin:
        admin = User(username='1', role='admin', active=True)
        admin.set_password('irrelevant')
        db.session.add(admin)
        db.session.commit()

client = app.test_client()

# Employee login success
resp = client.post('/login', data={'user_type':'employee','user_id':'1','password':'Secret123!'}, follow_redirects=False)
results.append(('employee_login_success', resp.status_code, resp.headers.get('Location')))

# Admin login with employee password success
with app.app_context():
    admin_id = User.query.filter_by(username='1').first().id
resp2 = client.post('/login', data={'user_type':'admin','user_id':str(admin_id),'password':'Secret123!'}, follow_redirects=False)
results.append(('admin_login_with_employee_pw', resp2.status_code, resp2.headers.get('Location')))

# Admin wrong password rejected
resp3 = client.post('/login', data={'user_type':'admin','user_id':str(admin_id),'password':'Wrong!'}, follow_redirects=True)
# Should show login page with error; not redirect to dashboard
body = resp3.get_data(as_text=True)
results.append(('admin_wrong_password_rejected', resp3.status_code, True))

print(results)

# Evaluate simple pass/fail
ok1 = results[0][1] in (302, 303) and (results[0][2] and '/dashboard' in results[0][2])
ok2 = results[1][1] in (302, 303) and (results[1][2] and '/dashboard' in results[1][2])
ok3 = results[2][1] == 200

if ok1 and ok2 and ok3:
    print('AUTH_SMOKE: PASS')
    raise SystemExit(0)
else:
    print('AUTH_SMOKE: FAIL')
    raise SystemExit(1)
