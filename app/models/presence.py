from app import db
from datetime import datetime

class EmployeePresence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
    status = db.Column(db.String(16), default='offline')  # 'online', 'away', 'offline'
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    session_start = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
