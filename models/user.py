from database import db

class User(db.Model):
    id = db.Column(db.Integer)
    facebook_id = db.Column(db.Integer, primary_key=True)
    google_credentials = db.Column(db.String)

    def __init__(self, facebook_id):
        self.facebook_id = facebook_id

    def __repr__(self):
        return str(self.facebook_id)