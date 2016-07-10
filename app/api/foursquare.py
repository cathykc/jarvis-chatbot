from flask import redirect
import requests
from requests.auth import HTTPBasicAuth
from app.models import User, Event
from database import db

def setup(request, facebook_id):
    authorization_code = request.args.get('code')

    client_id = 'MEZC4SKNQBXGVTMXMW0IKILIW1RQ4CAZ5AOQROEB5JGLGGD0'
    client_secret = 'DZKA31MFCNC252LAAKV05XVQIWWM0IWBQCGQU3L2IEA43JJD'
    redirect_uri = 'http://127.0.0.1:5000/foursquare_redirect'

    # Get access token
    token_url = 'https://foursquare.com/oauth2/access_token?client_id='+client_id+'&client_secret='+client_secret+'&grant_type=authorization_code&redirect_uri='+redirect_uri+'&code=' + authorization_code
    r = requests.get(token_url)
    if 'access_token' in r.json():
        access_token = r.json()['access_token']

    print 'GOT FOURSQUARE ACCESS TOKEN'
    print access_token

    print facebook_id

    user = User.query.get(facebook_id)
    if not user:
        print 'false'
        return False

    user.foursqure_access_token = access_token

    db.session.add(user)
    try:
        print 'commiting'
        db.session.commit()
    except IntegrityError:
        db.session.rollback()

    # Redirect to dashboard
    redirect_url = "/" + facebook_id
    return redirect(redirect_url)