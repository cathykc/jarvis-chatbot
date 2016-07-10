from datetime import datetime, timedelta
import pytz
import json
import flask
import httplib2

from apiclient import discovery
from oauth2client import client
from database import db
from app import User

def oauth(facebook_id):
    user = User.query.get(facebook_id)
    flask.session['facebook_id'] = facebook_id
    if not user:
        return "User not found"
    print "google credentials", user.google_credentials
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
        if 'redirect_uri=https' in auth_uri:
            auth_uri.replace('redirect_uri=https', 'redirect_uri=http')
        return flask.redirect(auth_uri)
    else:
        auth_code = flask.request.args.get('code')
        credentials = flow.step2_exchange(auth_code)
        user = User.query.get(facebook_id)
        if not user:
            return "User not found"
        user.google_credentials = json.dumps(credentials.to_json())
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        print "Authenticated User for Google!"
        return flask.redirect(flask.url_for('dashboard', facebook_id=facebook_id))

def now():
    return datetime.now()

def minutes_later(original_datetime, minutes):
    print "before"
    print original_datetime
    print "-------++"
    print timedelta(minutes=minutes)
    temp = original_datetime + timedelta(minutes=minutes)
    print "after"
    return temp

def minutes_before(original_datetime, minutes):
    return (original_datetime - timedelta(minutes=minutes))

# hour out of 24
def today_at(hour, minute):
    return datetime.now().replace(hour=hour, minute=minute)

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
    else:
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print event
            print event['end']
            end = event['end'].get('dateTime', event['end'].get('date'))

            start = datetime.strptime(start.split("T")[1].split("-")[0], "%H:%M:%S")
            end = datetime.strptime(end.split("T")[1].split("-")[0], "%H:%M:%S")

            eventObj = {
                "location": event['location'] if 'location' in event else None,
                "start_time": start.strftime("%I:%M %p"), 
                "end_time": end.strftime("%I:%M %p"),
                "title": event["summary"]
            }
            output.append(eventObj)
    return output
    
# summary: String, location: String, start_time: datetime string, emails: [String]
# returns true on success i hope
def create_event(facebook_id, summary, location, start_time, end_time, emails):
    user = User.query.get(facebook_id)
    if not user or not user.google_credentials:
        return False
    credentials = client.OAuth2Credentials.from_json(json.loads(user.google_credentials))
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    attendees = []
    for email in emails:
        attendees.append({
            'email': email
        })
    event = {
        'summary': summary,
        'location': location,
        'start': {
            'dateTime': start_time,
            'timeZone': 'America/Los_Angeles'
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'America/Los_Angeles'
        },
        'attendees': attendees
    }

    created_event = service.events().insert(calendarId='primary', body=event).execute()
    return True

# overlapping events will lead to unpredictable behavior
def get_free_time(facebook_id, interval_length_in_sec, start_time, end_time, events):
    now = datetime.now()
    if start_time is None:
        start_time = now
    today = datetime.today()
    start_of_today = datetime(today.year, today.month, today.day)
    end_of_today = start_of_today + timedelta(days=1) # Timezone difference
    if end_time is None:
        end_time = end_of_today

    if events is None or len(events) == 0:
        return [(now, end_of_today)]
    output = []
    last_end_time = start_time
    for event in events:
        next_start_time = datetime.strptime(event['start_time'], "%I:%M %p")
        print next_start_time - last_end_time
        if (next_start_time - last_end_time) > timedelta(seconds=interval_length_in_sec):
            output.append((last_end_time, next_start_time))
        last_end_time = datetime.strptime(event['end_time'], "%I:%M %p")
    return output
    
