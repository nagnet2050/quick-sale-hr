from app import db
from datetime import datetime

class LeaveBalance(db.Model):
    __tablename__ = 'leave_balance'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), unique=True, nullable=False)

    annual_total = db.Column(db.Integer, default=21)
    annual_used = db.Column(db.Integer, default=0)

    casual_total = db.Column(db.Integer, default=6)
    casual_used = db.Column(db.Integer, default=0)

    # sick paid policy (cap per year)
    sick_paid_cap = db.Column(db.Integer, default=0)  # 0 means unlimited/disabled
    sick_used_paid = db.Column(db.Integer, default=0)

    # tracking
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def annual_available(self):
        return max(0, int(self.annual_total or 0) - int(self.annual_used or 0))

    @property
    def casual_available(self):
        return max(0, int(self.casual_total or 0) - int(self.casual_used or 0))

    @property
    def sick_paid_remaining(self):
        cap = int(self.sick_paid_cap or 0)
        if cap <= 0:
            return None
        return max(0, cap - int(self.sick_used_paid or 0))
