from app import db
from datetime import datetime

class SupportTicket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_phone = db.Column(db.String(32), nullable=False)
    customer_name = db.Column(db.String(128), nullable=False)
    issue = db.Column(db.Text, nullable=False)
    resolved_by_employee = db.Column(db.Boolean, default=False)
    shown_to_management = db.Column(db.Boolean, default=False)
    resolved_by_management = db.Column(db.Boolean, default=False)
    management_response = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
