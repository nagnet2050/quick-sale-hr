from app import db
from datetime import datetime


class Audit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)
    action = db.Column(db.String(64), nullable=False)
    object_type = db.Column(db.String(64), nullable=False)
    object_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
