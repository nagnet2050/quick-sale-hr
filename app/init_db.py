from app import create_app, db
from app.models.user import User
from app.models.employee import Employee
from app.models.attendance import Attendance
from app.models.settings import Settings

app = create_app()
with app.app_context():
    db.create_all()
    print('Database initialized.')
