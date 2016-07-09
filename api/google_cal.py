import json
import flask
import httplib2

from apiclient import discovery
from oauth2client import client

def oauth():
  if 'google_credentials' not in flask.session:
    return flask.redirect(flask.url_for('google_oauth2callback'))
    # Getting credentials from flask.session
  credentials = client.OAuth2Credentials.from_json(flask.session['google_credentials'])
  if credentials.access_token_expired:
    return flask.redirect(flask.url_for('google_oauth2callback'))
  else:
    # Already oauthed.
    http_auth = credentials.authorize(httplib2.Http())
    drive_service = discovery.build('drive', 'v2', http_auth)
    files = drive_service.files().list().execute()
    return json.dumps(files)

def oauth2callback():
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
    flask.session['google_credentials'] = credentials.to_json()
    return flask.redirect(flask.url_for('dashboard'))

def events_today():
    credentials = client.OAuth2Credentials.from_json(flask.session['google_credentials'])
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print 'Getting the upcoming 10 events'
    eventsResult = service.events().list(
        calendarId='primary', timeMin=now, maxResults=10, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    if not events:
        print 'No upcoming events found.'
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print start, event['summary']
