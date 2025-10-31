from app import db

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
    check_in_time = db.Column(db.DateTime)
    check_out_time = db.Column(db.DateTime)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    address = db.Column(db.String(256))
    status = db.Column(db.String(32))  # 'inside' or 'outside'
    date = db.Column(db.Date)
