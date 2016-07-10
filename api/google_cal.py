from datetime import datetime, timedelta
import pytz
import json
import flask
import httplib2

from apiclient import discovery
from oauth2client import client
from database import db
from models import User

def oauth(facebook_id):
    flask.session['facebook_id'] = facebook_id 
    # Getting credentials from flask.session
    user = User.query.get(facebook_id)
    if not user:
        return "User not found"
    print "google credentials", user.google_credentials
    # used to be flask.session['google_credentials']
    if not user.google_credentials:
        return flask.redirect(flask.url_for('google_oauth2callback'))       
    credentials = client.OAuth2Credentials.from_json(json.loads(user.google_credentials))
    if credentials.access_token_expired:
        return flask.redirect(flask.url_for('google_oauth2callback'))
    else:
        # Already oauthed.
        return "Already oauthed"

def oauth2callback(facebook_id):
    flow = client.flow_from_clientsecrets(
        'google_client_secrets.json',
        scope='https://www.googleapis.com/auth/calendar',
        redirect_uri=flask.url_for('google_oauth2callback', _external=True))
    if 'code' not in flask.request.args:
        auth_uri = flow.step1_get_authorize_url()
        return flask.redirect(auth_uri)
    else:
        auth_code = flask.request.args.get('code')
        credentials = flow.step2_exchange(auth_code)
        # Storing credentials in flask.session
        user = User.query.get(facebook_id)
        if not user:
            return "User not found"
        user.google_credentials = json.dumps(credentials.to_json())
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        #flask.session['google_credentials'] = credentials.to_json()
        return flask.redirect(flask.url_for('dashboard', facebook_id=facebook_id))

def get_events_today(facebook_id):
    user = User.query.get(facebook_id)
    if not user or not user.google_credentials:
        return "Permission denied. Please OAuth for Google Calendar."
    credentials = client.OAuth2Credentials.from_json(json.loads(user.google_credentials))
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    today = datetime.today()
    start_of_today = datetime(today.year, today.month, today.day)
    end_of_today = start_of_today + timedelta(days=1, hours=8) # Timezone difference
    print end_of_today
    end_of_today_iso = end_of_today.isoformat() + 'Z'
    print 'Getting the upcoming events for today'
    eventsResult = service.events().list(
        calendarId='primary', timeMin=now, timeMax=end_of_today_iso, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])
    output = []
    if not events:
        print 'No upcoming events found.'
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print start, event['summary']
        output.append(event['summary'])
    return ", ".join(output)
    
