from app import db

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), unique=True, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    job_title = db.Column(db.String(64))
    department = db.Column(db.String(64))
    phone = db.Column(db.String(32))
    email = db.Column(db.String(128))
    active = db.Column(db.Boolean, default=True)
    salary = db.Column(db.Float, default=0.0)
