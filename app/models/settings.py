from app import db

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_lat = db.Column(db.Float)
    company_lng = db.Column(db.Float)
    work_start = db.Column(db.String(8))
    work_end = db.Column(db.String(8))
    presence_interval_min = db.Column(db.Integer)
    presence_grace_min = db.Column(db.Integer)
    presence_sound_enabled = db.Column(db.Boolean)
