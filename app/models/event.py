from database import db

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    facebook_id = db.Column(db.BigInteger)
    
    send_timestamp = db.Column(db.DateTime)
    metadata_json = db.Column(db.Text)

    trigger_enum = db.Column(db.Integer)
    # 1 - morning info card
    # 2 - morning lyft
    # 3 - afternoon lyft
    # 4 - walking reminder
    # 5 - driving reminder
 
    def __init__(self, facebook_id):
        self.facebook_id = facebook_id

    # def __repr__(self):
    #     return str(self.facebook_id)