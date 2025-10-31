from app import db

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    report_type = db.Column(db.String(32))
    generated_at = db.Column(db.DateTime)
    data = db.Column(db.Text)
