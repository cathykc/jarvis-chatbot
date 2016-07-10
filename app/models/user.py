from database import db

class User(db.Model):
    id = db.Column(db.Integer)
    facebook_id = db.Column(db.BigInteger, primary_key=True)
    google_credentials = db.Column(db.String)

    lyft_access_token = db.Column(db.String)
    lyft_refresh_token = db.Column(db.String)
    
    lyft_home_address = db.Column(db.String)
    lyft_home_lat = db.Column(db.Float)
    lyft_home_long = db.Column(db.Float)
    lyft_go_home_time = db.Column(db.DateTime)

    lyft_work_address = db.Column(db.String)
    lyft_work_lat = db.Column(db.Float)
    lyft_work_long = db.Column(db.Float)
    lyft_go_to_work_time = db.Column(db.DateTime)

    reminders = db.Column(db.String)

    foursquare_access_token = db.Column(db.String)


    def __init__(self, facebook_id):
        self.facebook_id = facebook_id

    def __repr__(self):
        return str(self.facebook_id)