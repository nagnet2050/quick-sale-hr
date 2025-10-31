from app import create_app, db
from app.models.employee import Employee
from app.models.attendance import Attendance

app = create_app()
with app.app_context():
    # Add demo employees
    employees = [
        Employee(code='E001', name='أحمد محمد', job_title='مدير', department='إدارة', phone='0500000001', email='ahmed@example.com', active=True),
        Employee(code='E002', name='Sara Ali', job_title='HR', department='موارد بشرية', phone='0500000002', email='sara@example.com', active=True),
    ]
    db.session.bulk_save_objects(employees)
    db.session.commit()
    print('Demo employees added.')
    # Add demo attendance
    # ...
