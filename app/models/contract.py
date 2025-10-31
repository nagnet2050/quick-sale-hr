from app import db

class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    contract_type = db.Column(db.String(32))
    details = db.Column(db.Text)
