from app import db
from datetime import datetime, timedelta


class PasswordResetCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(128), nullable=False)
    code = db.Column(db.String(12), nullable=False)  # 6-digit code (string)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    attempts = db.Column(db.Integer, default=0)

    @staticmethod
    def generate(employee_id, email, ttl_minutes=10):
        import random
        code = f"{random.randint(100000, 999999)}"
        reset = PasswordResetCode(
            employee_id=employee_id,
            email=email.strip(),
            code=code,
            expires_at=datetime.utcnow() + timedelta(minutes=ttl_minutes),
        )
        db.session.add(reset)
        return reset
