from database import db
from app.models import User, Event
import app
from flask import Flask, request, render_template, session, url_for
from app.api import google_cal, yelp_api, lyft, nyt_api, weather_api, foursquare, google_maps
from sqlalchemy.exc import IntegrityError
import json
import requests
import os
import uuid
import parse_query
from datetime import datetime, timedelta
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') if os.environ.get('DATABASE_URL') else "sqlite:////tmp/test.db"
db.init_app(app)
app.secret_key = str(uuid.uuid4())

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)

# *****************************************************************************
# WEBAPP ROUTES
# *****************************************************************************


@app.route("/")
@app.route("/<facebook_id>")
def dashboard(facebook_id=None):
    # I have never done something so hacky in my life @cathy
    if facebook_id == 'favicon.ico':
        return ""
    if facebook_id == None:
        return render_template('login.html')
    session['fbid'] = facebook_id
    user = User.query.get(facebook_id)
    if not user:
        user = User(facebook_id=facebook_id) 
        db.session.add(user)
        print user, "new user added"
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

    # Check if lyft is connected
    lyft_connected_flag = False
    if user.lyft_access_token is not None:
        lyft_connected_flag = True

    # Check if google cal is connected
    google_cal_connected_flag = False
    if user.google_credentials is not None:
        google_cal_connected_flag = True

    # Check if foursquare is connected
    foursquare_connected_flag = False
    if user.foursquare_access_token is not None:
        print 'foursquare connected'
        foursquare_connected_flag = True
    else:
        print 'foursquare NOT connected'

    return render_template('dashboard.html', facebook_id=facebook_id, lyft_connected_flag=lyft_connected_flag, google_cal_connected_flag=google_cal_connected_flag,foursquare_connected_flag=foursquare_connected_flag)

# Foursquare webhook 
@app.route("/foursquare_push", methods=['GET','POST'])
def foursquare_push():
    checkin_obj = request.form.get('checkin')

    # venue_name = checkin_obj['venue']['name']
    # venue_city = checkin_obj['venue']['city']

    # Schedule a notification for ice cream in 1 hour
    food_type = 'Ice Cream'
    location = 'Menlo Park'
    response = yelp_api.get_top_locations_swarm(food_type, 5, location)
    sendTextMessage('1243735802327809', "Since you are in Menlo park, here are the best places to get " +
                    food_type + " around you: ")
    sendCarouselMessage('1243735802327809', response)

    return ''

@app.route("/scheduler/<facebook_id>")
def scheduler(facebook_id=None):
    events = Event.query.filter_by(facebook_id=facebook_id).all()

    return render_template('scheduler.html', facebook_id=facebook_id, events=events)

def lyft_request_ride(facebook_id, isMorning):

    # Get the user
    user = User.query.get(facebook_id)
    if not user:
        return False

    # Determine pickup and dropoff based on home, work, and isMorning flag
    rideType = 'lyft_line'

    if isMorning:
         # Retrieve work as destination
         pickupLat = user.lyft_home_lat
         pickupLong = user.lyft_home_long
         dropoffLat = user.lyft_work_lat
         dropoffLong = user.lyft_work_long
    else:
         # Retrieve home as destination
         pickupLat = user.lyft_work_lat
         pickupLong = user.lyft_work_long
         dropoffLat = user.lyft_home_lat
         dropoffLong = user.lyft_home_long

    access_token = user.lyft_access_token
    refresh_token = user.lyft_refresh_token

    # Request ride
    lyft.request_ride(access_token, refresh_token, pickupLat, pickupLong, dropoffLat, dropoffLong, rideType)

    return isMorning
    

@app.route("/lyft_auth_redirect")
def lyft_auth():
    facebook_id = request.args.get('state')
    if facebook_id == None:
        return render_template('login.html')
    return lyft.setup(request, facebook_id)

@app.route("/foursquare_redirect/<facebook_id>")
def foursquare_auth(facebook_id=None):
    if facebook_id == None:
        return render_template('login.html')
    return foursquare.setup(request, facebook_id)

@app.route("/google_auth/<facebook_id>")
def google_auth(facebook_id=None):
    if facebook_id == None:
        return render_template('login.html')
    session['facebook_id'] = facebook_id
    return google_cal.oauth(facebook_id)

@app.route("/google_oauth2callback")
def google_oauth2callback():
    facebook_id = session['facebook_id']
    if facebook_id == None:
        return render_template('login.html')
    return google_cal.oauth2callback(facebook_id)

@app.route("/fitbit_auth")
def fitbit_auth():
    return "FITBIT AUTH"

# simulates a text message event
@app.route("/message_test/<facebook_id>/<message>")
def message_test(facebook_id=None, message=""):
    event = {}
    event['sender'] = {}
    event['message'] = {}
    event['sender']['id'] = facebook_id
    event['message']['text'] = message
    receivedMessage(event)
    return "Check your server logs"

# *****************************************************************************
# DEMO TRIGGER ENDPOINTS
# *****************************************************************************
@app.route("/lyft_trigger")
def lyft_trigger():
    facebook_id = request.args.get('facebook_id')
    sendLyftCTA(facebook_id)    
    return ""

@app.route("/scheduler_trigger/<event_id>")
def scheduler_trigger(event_id=None):
    event = Event.query.get(event_id)

    facebook_id = event.facebook_id
    enum = event.trigger_enum

    if enum == 1:
        # Morning info card
        sendMorningCard(facebook_id)
    elif enum == 2:
        # Morning commute
        sendLyftCTA(facebook_id, True) 
    elif enum == 3:
        # Evening commute
        sendLyftCTA(facebook_id, False) 
    elif enum == 4:
        metadata = json.loads(event.metadata_json)
        sendWalkingMessage(facebook_id, metadata)
        db.session.delete(event)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
    elif enum == 5:
        metadata = json.loads(event.metadata_json)
        sendDrivingMessage(facebook_id, metadata)
        db.session.delete(event)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
    else:
        sendTextMessage(facebook_id, "wasn't handled")
    return ''



# *****************************************************************************
# CHATBOT WEBHOOK
# *****************************************************************************

# please excuse pulic keys - to move soon
# APP_SECRET = "763bc897c7ab402b870ad33a7cd59062"
# VALIDATION_TOKEN = "jarvis"
# PAGE_ACCESS_TOKEN = "EAANTFr9A1IEBAFi3QsRXDkZBl5yVYZC5XrCuqUxZCXDcc2Y9rD3LEqAtdqhpNHZAfZAWUVCzh9XmZCKcTV3ZBPIuH4ChfqfYaIkha2zLsazbyxoB8vJKFwr0qbwtwO7lbZBsiOgXfGjKq5zTmJvKrmnxKYqkmZCRZAnv1XKqlZCK4cnEQZDZD"
APP_SECRET = os.environ.get('MESSENGER_APP_SECRET') if os.environ.get('MESSENGER_APP_SECRET') else "763bc897c7ab402b870ad33a7cd59062"
VALIDATION_TOKEN = os.environ.get('MESSENGER_VALIDATION_TOKEN') if os.environ.get('MESSENGER_VALIDATION_TOKEN') else "jarvis"
PAGE_ACCESS_TOKEN = os.environ.get('MESSENGER_PAGE_ACCESS_TOKEN') if os.environ.get('MESSENGER_PAGE_ACCESS_TOKEN') else "EAANTFr9A1IEBAFi3QsRXDkZBl5yVYZC5XrCuqUxZCXDcc2Y9rD3LEqAtdqhpNHZAfZAWUVCzh9XmZCKcTV3ZBPIuH4ChfqfYaIkha2zLsazbyxoB8vJKFwr0qbwtwO7lbZBsiOgXfGjKq5zTmJvKrmnxKYqkmZCRZAnv1XKqlZCK4cnEQZDZD"



@app.route("/webhook", methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        print "post called"
        try:
            data = json.loads(request.data)
            for entry in data['entry']:
                for message in entry['messaging']:
                    if 'optin' in message:
                        pass
                    elif 'message' in message:
                        print " IN MESSAGE MESSAGE"
                        receivedMessage(message)
                    elif 'delivery' in message:
                        pass
                    elif 'postback' in message:
                        receivedPostback(message)
                    else:
                        print "Webhook received unknown message."

        except Exception:
            return "Something went wrong"
        return "Yay", 200

    elif request.method == 'GET':
        print "get called"
        if (request.args.get('hub.mode') == 'subscribe' and
                request.args.get('hub.verify_token') == VALIDATION_TOKEN):
            return request.args.get('hub.challenge'), 200
        else:
            print "**********"
            print request.args.get('hub.mode')
            print request.args.get('hub.verify_token')
            print request
            return "Wrong Verify Token", 403


# *****************************************************************************
# CHATBOT MESSAGING AND POSTBACKS
# *****************************************************************************

def receivedMessage(event):
    facebook_id = event['sender']['id']
    message = event['message']

    print "--------------------------------"
    print message
    r = requests.get("https://graph.facebook.com/v2.6/" + str(facebook_id) + "?fields=first_name&access_token=" + PAGE_ACCESS_TOKEN)
    first_name = r.json()["first_name"]

    if 'text' in message:
        text = message["text"].lower()

        if 'ping' in text:
            sendTextMessage(facebook_id, "pong")
        elif 'hello' in text:
            sendTextMessage(facebook_id, "hello, world!")
        elif 'morning card' in text:
            sendMorningCard(facebook_id)

        elif 'weather' in text:
            sendWeather(facebook_id)

        elif 'gym' in text or 'grocery' in text:
            # response = google_cal.get_free_time(facebook_id, 3600, None, None)
            sendFreeTimeMessage(first_name, "gym", facebook_id, 3600, None,
                                None)

        elif 'test distance please' in text:
            google_maps.walking_time_from_home(
                facebook_id,
                "1 Hacker Way"
            )
        elif 'remind' in text:
            print 'IN REMINDER ELIF!!!'
            user = User.query.get(facebook_id)
            print('1')
            task = text.replace('remind me to ', '')
            print('2')
            print(user.reminders)
            print(task)
            if user.reminders is None:
                user.reminders = task
            else:
                user.reminders = user.reminders + '$'+task
            print('3')
            db.session.add(user)
            try:
                print 'saving'
                db.session.commit()
            except IntegrityError:  
                print 'error'
                db.session.rollback()

            print 'right before sending text message'
            sendTextMessage(facebook_id, "Done - I'll remind you during your ride home tonight to " + task)
        elif 'fuck' in text or 'shit' in text or 'damn' in text:
            sendTextMessage(facebook_id, "Watch your language!")

        elif 'hey' in text or text == 'hi':
            sendTextMessage(facebook_id, "Hey, " + first_name + "!")

        elif 'how are you' in text or 'how are you' in text or 'how\'re you' \
                in text:
            sendTextMessage(facebook_id, "I'm good! I hope you are, too!")

        elif "my events" in text:
            sendEventDigest(facebook_id)

        elif "event right now" in text:
            google_cal.create_event(
                facebook_id, 
                "Test Event",
                "1 Hacker Way",
                google_cal.now().isoformat(),
                google_cal.minutes_later(datetime.now(), 60).isoformat(),
                ["danielzh@sas.upenn.edu"]
            )
            sendTextMessage(facebook_id, "Scheduling an event right now!")

       # elif "get free time for gym" in text:
            # any time today for an hour
       #     sendFreeTimeMessage(first_name, "gym", facebook_id, 3600, None,
       # None)

        elif "event at 7" in text:
            google_cal.create_event(
                facebook_id, 
                "Test Event",
                "1 Hacker Way",
                google_cal.today_at(19, 0).isoformat(),
                google_cal.minutes_later(google_cal.today_at(19, 0), 60).isoformat(),
                ["danielzh@sas.upenn.edu"]
            )
            sendTextMessage(facebook_id, "Scheduling an event at 7!")

        elif 'schedule' in text:
            split = text.split()
            location = parse_query.getPlace(text)
            food_type = parse_query.getFood(text)
            if food_type is None:
                sendTextMessage(facebook_id, "Tell me what type of food you want to "
                                          "schedule! Ex: 'scheudle coffee in "
                                          "San Francisco")
                return
            elif location is None:
                sendTextMessage(facebook_id, "Where do you want " +
                                food_type + "? Try saying: 'schedule " +
                                food_type + " in San Francisco' ")
                return

            who = parse_query.getPerson(text)
            time = parse_query.getTime(text)
            print time
            if time is None:
                parsed_time = None
            elif "am" in time or "pm" in time:
                just_num = time[:-2]
                just_num.strip()
                print just_num
                if 'am' in time:
                    num_time = int(just_num)
                else:
                    num_time = int(just_num) + 12
                parsed_time = google_cal.today_at(num_time, 0).isoformat()
            elif "a.m." in time or "p.m." in time:
                just_num = time[:-4]
                just_num.strip()
                print just_num
                if 'a.m.' in time:
                    num_time = int(just_num)
                else:
                    num_time = int(just_num) + 12
                parsed_time = google_cal.today_at(num_time, 0).isoformat()
            else:
                num_time = int(time)
                parsed_time = google_cal.today_at(num_time, 0).isoformat()
            response = yelp_api.get_top_locations(food_type, 3, location,
                                                  parsed_time, who)
            sendTextMessage(facebook_id, "Here are the best places to get " +
                            food_type + "in " + location + ":  ")
            sendCarouselMessage(facebook_id, response)

        elif 'more articles' in text:
            response = nyt_api.get_top_articles(10)
            sendTextMessage(facebook_id, "I've added five more "
                                           "news stories for you! ")
            sendCarouselMessage(facebook_id, response)

        elif 'news' in text:
            response = nyt_api.get_top_articles(5)
            sendTextMessage(facebook_id, "Here are todays five most popular "
                                         "news stories: ")
            sendCarouselMessage(facebook_id, response)

        elif 'help me' in text:
            help = "Try asking me to do the following commands:\n\n- news\n- my events\n weather"
            sendTextMessage(facebook_id, help)

        elif 'hey jarvis' in text:
            sendTextMessage(facebook_id, "Hey, " + first_name + "!")

        elif "what's up" in text or "whats up" in text:
            sendTextMessage(facebook_id, "Not much! Hope you're having a "
                                         "good day, "+first_name + "!")

        elif 'who am i' in text or 'whats my name' in text or "what's my " \
                                                              "name" in text:
            sendTextMessage(facebook_id, "You are " + first_name + "!")

        elif 'knock knock' in text:
            sendTextMessage(facebook_id, "Who's there?! I'm Jarvis!")

        elif 'do you have free will' in text:
            sendTextMessage(facebook_id, "Yes.")

        elif 'what is your name' in text or 'who are you' in text or 'whats ' \
                                                                     'your ' \
                                                                     'name' \
                in text:
            sendTextMessage(facebook_id, "My name is Jarvis!")

        else:
            sendTextMessage(facebook_id, "Sorry, I don't quite understand what "
                                         "you "
                                         "said! Type  \'help me\' for help.")

    elif 'attachments' in message:
        sendTextMessage(facebook_id, "Attachment received.")

# Pass in the message string and then arrays of text choices
# e.g. matchType("schedule event", ["schedule", "plan"], ["event", "something"])
# Not tested sorry guys don't kill me
def matchType(text, *and_args):
    for or_args in and_args:
        found = False
        for word in or_args:
            if word in text:
                found = True
                break
        if not found:
            return False
    return True



def receivedPostback(event):
    facebook_id = event['sender']['id']
    payload = event['postback']['payload']

    if payload is None or payload == "noop" or payload == "SCHEDULE_EVENT":
        sendTextMessage(facebook_id, "Sounds good!")
        return

    if payload == "GET_STARTED":
        r = requests.get("https://graph.facebook.com/v2.6/" + str(facebook_id) + "?fields=first_name&access_token=" + PAGE_ACCESS_TOKEN)
        
        dashboard_url = "http://jarvis-chatbot.herokuapp.com/" + facebook_id

        element = {"title": "Hi " + r.json()["first_name"] + ", nice to meet you!"}
        element["subtitle"] = "Set me up by visiting the Jarvis Dashboard."
        element["item_url"] = dashboard_url
        element["image_url"] = "https://easilydo.files.wordpress.com/2014/03/ownpersonalasst-bloggraphic.jpg"
        element["buttons"] = [{"type": "web_url", "url": dashboard_url, "title": "Set Up Accounts"}]

        sendCarouselMessage(facebook_id, [element])
    elif 'CALL_LYFT' in payload:
        # Request ride
        print "CALLING LYFT HERE"
        isMorning = ("work" in payload)
        lyft_request_ride(facebook_id, isMorning)

        if isMorning:
            print 'MORNING'
            sendTextMessage(facebook_id, "I got you a Lyft to work, it'll be here in a few minutes! Also, check out what's going on in the world while you wait:")
            
            # Send news
            response = nyt_api.get_top_articles(5)
            sendCarouselMessage(facebook_id, response)
        else:
            print 'AFTERNOON REMINDERS'
            # Prep reminders
            reminders_string = ''
            print 'reminders_string'
            print reminders_string

            reminders = User.query.get(facebook_id).reminders
            if reminders is not None:
                reminders_list = reminders.split('$')
                for reminder in reminders_list:
                    if reminder != '':
                        reminders_string += '- ' + reminder + '\n'

            sendTextMessage(facebook_id, "I got you a Lyft home, it'll be here in a few minutes.")
            
            if reminders_string != '':
                reminders_string = 'Here\'s what you wanted me to remind you about today:\n\n' + reminders_string 
                sendTextMessage(facebook_id, reminders_string)
        

    # create cal event from yelp
    else:
        print payload
        parsed = json.loads(payload)
        if 'payload' in parsed:
            if parsed['payload'] == 'WALK':
                drive_id = parsed['drive_id']
                event = Event.query.get(drive_id)
                if event is None:
                    return
                db.session.delete(drive_id)
                try:
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()

                #Get scheduled async, remove it
        print parsed['address']
        print parsed['title']
        if parsed['time'] is None:
            print "time is none"
            time = google_cal.now()
            end_time = google_cal.minutes_later(time, 30).isoformat()
        else:
            time = parsed['time']
            print "IN PAYLOAD"
            print time
            d = datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%f")
            end_time = google_cal.minutes_later(d, 60).isoformat()
            start_to_cal = d.isoformat()
            print start_to_cal
            print end_time
            print parsed['summary']
        if parsed['person'] is None:
            emails = []
        else:
            emails = []
        print 'ALMOST THERE'
        google_cal.create_event(facebook_id, parsed['summary'],
                                parsed['address'], start_to_cal, end_time, emails)
        sendTextMessage(facebook_id, "Putting this event into your calendar!")

# *****************************************************************************
# MESSAGE CREATION FUNCTION DUMP
# *****************************************************************************

def sendWalkingMessage(facebook_id, metadata):
    payload = {
        'payload': "WALK",
        'drive_id': metadata['drive_id']
    }
    buttonList = [{
            'type': "postback",
            'title': "I'll walk!",
            'payload': json.dumps(payload)
        }, {
            'type': "postback",
            'title': "I'll drive.",
            'payload': "noop"
        }
    ]
    sendButtonMessage(
        facebook_id,
        metadata['title'] + " is starting soon - you should start walking now!",
        buttonList
    )

def sendDrivingMessage(facebook_id, metadata):
    buttonList = [{
            'type': "postback",
            'title': "Call me a Lyft",
            'payload': "CALL_LYFT HOME"
        }, {
            'type': "postback",
            'title': "I'll drive.",
            'payload': "noop"
        }
    ]
    
    sendButtonMessage(
        facebook_id,
        metadata['title'] + " is starting soon - you should call a Lyft!",
        buttonList
    )

def sendFreeTimeMessage(first_name, event_name, facebook_id, interval_length_in_sec, start_time, end_time):
    free_intervals = google_cal.get_free_time(facebook_id, interval_length_in_sec, start_time, end_time)
    if len(free_intervals) == 0:
        sendTextMessage(facebook_id, "Sorry {}, it seems like you don't have time today.".format(first_name))
    else:
        buttonList = []
        for interval in free_intervals:
            buttonList.append({
                'type': "postback",
                'title': interval[0].strftime("%I:%M %p") + " - " + interval[1].strftime("%I:%M %p"),
                'payload': "SCHEDULE_EVENT"
            })
        sendButtonMessage(
            facebook_id,
            "Here are some times you're free!".format(event_name),
            buttonList
        )

def sendMorningCard(facebook_id):
    sendWeather(facebook_id)
    sendImageMessage(facebook_id, "http://static1.squarespace.com/static/547f29bfe4b0dc192ed7bdac/54aeb15ce4b018c14f34c7cb/54aeb160e4b018c14f34c7ed/1420734817363/san-franc.jpg?format=2500w")
    sendEventDigest(facebook_id)

def sendWeather(facebook_id):
    r = requests.get("https://graph.facebook.com/v2.6/" + str(facebook_id) + "?fields=first_name&access_token=" + PAGE_ACCESS_TOKEN)
    first_name = r.json()["first_name"]
    weather = weather_api.getWeatherConditions("San Francisco")
    sendTextMessage(facebook_id, "Good morning {}! Today in {} it is {} with a temperature of {}.".format(first_name, weather["city"], weather["weather"], weather["temperature"]))

def sendEventDigest(facebook_id):
    events = google_cal.get_events_today(facebook_id)
    print "sendEventDigest", events
    # also schedules all the async messages
    events_formatted = []
    for event in events:
        events_formatted.append(event["start_time"] + ": " + event["title"])
        scheduleCalReminderEvent(event, facebook_id)


    busy = am_i_busy(len(events))
    sendTextMessage(facebook_id, busy + "Here's what you're doing today:\n\n"+
                    "\n".join(events_formatted))

def scheduleCalReminderEvent(event, facebook_id):
    print "scheduling cal reminder events"
    print event
    if 'location' not in event or event['location'] is None:
        return False
    today = datetime.today()
    driving_time_in_sec = google_maps.driving_time_from_work(facebook_id, event['location'])['value']
    walking_time_in_sec = google_maps.walking_time_from_work(facebook_id, event['location'])['value']
    event_start_time = datetime.strptime(event['start_time'], "%I:%M %p")
    event_start_time = datetime(today.year, today.month, today.day, event_start_time.hour, event_start_time.minute, 0)
    driving_alert_time = event_start_time - timedelta(seconds=driving_time_in_sec)
    walking_alert_time = event_start_time - timedelta(seconds=walking_time_in_sec)

    driving_event = Event(facebook_id=facebook_id)
    driving_event.trigger_enum = 5
    driving_event.send_timestamp = driving_alert_time
    driving_event.metadata_json = json.dumps(event)

    walking_metadata = event.copy()
    walking_metadata['drive_id'] = driving_event.id

    walking_event = Event(facebook_id=facebook_id)
    walking_event.trigger_enum = 4
    walking_event.send_timestamp = walking_alert_time
    walking_event.metadata_json = json.dumps(walking_metadata)

    db.session.add(driving_event)
    db.session.add(walking_event)
    print "created driving and walking events!"
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return False
    return True

# This mesasge sends a Lyft deeplink CTA to a recipient through messenger
def sendLyftCTA(facebook_id, isMorning):
    if isMorning:
        buttonsList = [{
            "type" : "postback",
            "payload" : "CALL_LYFT work",
            "title" : "Lyft Me to Work"
        }]
        sendButtonMessage(facebook_id, 'Need a ride to work?', buttonsList)
    else:
        buttonsList = [{
            "type" : "postback",
            "payload" : "CALL_LYFT home",
            "title" : "Lyft Me Home"
        }]
        sendButtonMessage(facebook_id, 'Need a ride home?', buttonsList)

def am_i_busy(num):
    if num <= 2:
        return ""
    elif num <= 4:
        return "Looks like you're a little busy today! You have " + str(num) \
               + " events. "
    elif num >= 5:
        return "You're very busy today! You have" + num + "events! "

# *****************************************************************************
# CHATBOT MESSAGES
# *****************************************************************************

# Send a text mesage.
def sendTextMessage(facebook_id, messageText):

    messageData = {'recipient': {'id': facebook_id}}
    messageData['message'] = {'text': messageText}

    print messageText
    callSendAPI(messageData)


# Send an image message.
def sendImageMessage(facebook_id, imageUrl):
    messageData = {'recipient': {'id': facebook_id}}

    attachment = {'type': "image"}
    attachment['payload'] = {'url': imageUrl}
    messageData['message'] = {'attachment': attachment}

    callSendAPI(messageData)


# Send a button message.
# e.g. buttonList:
# [{
#     type: "web_url",
#     url: "https://www.oculus.com/en-us/rift/",
#     title: "Open Web URL"
# }, {
#     type: "postback",
#     title: "Call Postback",
#     payload: "Developer defined postback"
# }]
def sendButtonMessage(facebook_id, messageText, buttonList):
    messageData = {"recipient": {"id": facebook_id}}

    attachment = {"type": "template"}
    attachment["payload"] = {"template_type":"button",
                             "text":messageText,
                             "buttons": buttonList}
    messageData['message'] = {'attachment':attachment}

    callSendAPI(messageData)


# Send a Carousel Message.
# e.g. elementList:
# [{
#     title: "rift",
#     subtitle: "Next-generation virtual reality",
#     item_url: "https://www.oculus.com/en-us/rift/",               
#     image_url: "http://messengerdemo.parseapp.com/img/rift.png",
#     buttons: [{
#         type: "web_url",
#         url: "https://www.oculus.com/en-us/rift/",
#         title: "Open Web URL"
#     }, {
#         type: "postback",
#         title: "Call Postback",
#         payload: "Payload for first bubble",
#     }],
# }, {
#     title: "touch",
#     subtitle: "Your Hands, Now in VR",
#     item_url: "https://www.oculus.com/en-us/touch/",               
#     image_url: "http://messengerdemo.parseapp.com/img/touch.png",
#     buttons: [{
#         type: "web_url",
#         url: "https://www.oculus.com/en-us/touch/",
#         title: "Open Web URL"
#     }, {
#         type: "postback",
#         title: "Call Postback",
#         payload: "Payload for second bubble",
#     }]
# }]

# elementList is a list of JSON objects
def sendCarouselMessage(facebook_id, elementList):
    messageData = {'recipient': {'id': facebook_id}}

    attachment = {'type': "template"}
    attachment['payload'] = {'template_type': "generic",
                             'elements': elementList}
    messageData['message'] = {'attachment': attachment}

    callSendAPI(messageData)


def callSendAPI(messageData):
    print "messageData", messageData
    r = requests.post(
        "https://graph.facebook.com/v2.6/me/messages/?access_token=" +
        PAGE_ACCESS_TOKEN,
        json=messageData
    )
    print r.json()
    if r.status_code == 200:
        print "Successfully sent message."
    else:
        print "Unable to send message."

@manager.command
def setup_db():
    with app.app_context():
    # print app
        db.drop_all()
        db.create_all()
        db.session.commit()
    print "database is set up!"


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    manager.run()
