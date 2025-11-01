from app import db


class Leave(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
    # leave_type codes: annual, weekly, holidays, casual, sick, unpaid, paid
    leave_type = db.Column(db.String(32))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    paid = db.Column(db.Boolean, default=True)  # هل الإجازة مدفوعة؟
    paid_days = db.Column(db.Integer)  # عدد الأيام المدفوعة (للنوع المرضي مع سقف)
    reason = db.Column(db.Text)  # سبب/ملاحظات
    status = db.Column(db.String(32))  # Approved/Pending/Rejected
    requested_at = db.Column(db.DateTime)
    approved_by = db.Column(db.Integer, nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
