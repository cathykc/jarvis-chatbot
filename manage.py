from database import db
from app.models import User
import app
from flask import Flask, request, render_template, session, url_for
from app.api import google_cal, yelp_api, lyft, nyt_api, weather_api
import json
import requests
import os
import uuid
import parse_query
from datetime import datetime
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
import datetime


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

    return render_template('dashboard.html', facebook_id=facebook_id, lyft_connected_flag=lyft_connected_flag, google_cal_connected_flag=google_cal_connected_flag)

def lyft_request_ride(facebook_id):
    # Determine what time of day it is
    current_datetime = datetime.datetime.now()
    if current_datetime.hour > 4 and current_datetime.hour < 12:
        isMorning = True
    else:
        isMorning = False

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
        return "Click in through Messenger"
    return lyft.setup(request, facebook_id)

@app.route("/google_auth/<facebook_id>")
def google_auth(facebook_id=None):
    if facebook_id == None:
        return "Click in through Messenger"
    return google_cal.oauth(facebook_id)

@app.route("/google_oauth2callback")
def google_oauth2callback():
    facebook_id = session['facebook_id']
    if facebook_id == None:
        return "Click in through Messenger"
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
    send_lyft_cta(facebook_id)    
    return "dd"

# This mesasge sends a Lyft deeplink CTA to a recipient through messenger
def send_lyft_cta(facebook_id):
    buttonsList = [{
        "type" : "postback",
        "payload" : "" + facebook_id,
        "title" : "Get me a Lyft home"
    }]
    sendButtonMessage(facebook_id, 'Need a ride to work?', buttonsList)


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

    # print facebook_id
    print "---------------------------------"
    print message
    r = requests.get("https://graph.facebook.com/v2.6/" + str(facebook_id) + "?fields=first_name&access_token=" + PAGE_ACCESS_TOKEN)
    first_name = r.json()["first_name"]

    if 'text' in message:
        text = message["text"].lower()

        if 'ping' in text:
             sendTextMessage(facebook_id, "pong")

        elif 'weather' in text:
            # TO DO : check if morning - hardcode morning for now
            # currently hard-coded (ideally get from lyft addrress)
            weather = weather_api.getWeatherConditions("San Francisco")
            sendTextMessage(facebook_id, "Good morning {}! Today in {} it is {} with a temperature of {}.".format(first_name, weather["city"], weather["weather"], weather["temperature"]))


        elif "my events" in text:
            sendTextMessage(facebook_id, google_cal.get_events_today(facebook_id))

        elif "event right now" in text:
            google_cal.create_event(
                facebook_id, 
                "Test Event",
                "1 Hacker Way",
                google_cal.now().isoformat(),
                google_cal.minutes_later(datetime.now(), 60).isoformat(),
                ["danielzh@sas.upenn.edu"]
            )

        elif "event at 7" in text:
            google_cal.create_event(
                facebook_id, 
                "Test Event",
                "1 Hacker Way",
                google_cal.today_at(19, 0).isoformat(),
                google_cal.minutes_later(google_cal.today_at(19, 0), 60).isoformat(),
                ["danielzh@sas.upenn.edu"]
            )

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

            response = yelp_api.get_top_locations(food_type, 3, location,
                                                  time, who)
            sendTextMessage(facebook_id, "Here are the best places to get " +
                            food_type + "in " + location + ":  ")


            sendCarouselMessage(facebook_id, response)

        elif 'news' in text:
            response = nyt_api.get_top_articles()
            sendCarouselMessage(facebook_id, response)

        elif 'help me' in text:
            help = "Try asking me to do the following commands: "
            sendTextMessage(facebook_id, help)

        elif 'lyft' in text:
            print("REACHED LYFTTTTTT")
            # Request ride
            isMorning = lyft_request_ride(facebook_id)

            if isMorning:
                sendTextMessage(facebook_id, "I got you a Lyft to work, it'll be here in a few minutes!")
            else:
                sendTextMessage(facebook_id, "I got you a Lyft home, it'll be here in a few minutes")

        elif 'hey jarvis' in text:
            sendTextMessage(facebook_id, "Hey, " + first_name + "!")

        elif 'who am i' in text or 'whats my name' in text or "what's my " \
                                                              "name" in text:
            sendTextMessage(facebook_id, "You are " + first_name + "!")

        elif 'knock knock' in text:
            sendTextMessage(facebook_id, "Who's there?! I'm Jarvis!")

        elif 'do you have free will' in text:
            sendTextMessage(facebook_id, "Yes.")

        elif 'fuck' in text or 'shit' in text or 'damn' in text:
            sendTextMessage(facebook_id, "Watch your language!")

        elif 'what is your name' in text or 'who are you' in text or 'whats ' \
                                                                     'your ' \
                                                                     'name' \
                in text:
            sendTextMessage(facebook_id, "My name is Jarvis!")

        else:
            sendTextMessage(facebook_id, "Sorry, I don't quite understand what "
                                         "you "
                                         "said! Type "
                                             "help me for help.")

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

    if payload == "GET_STARTED":
        r = requests.get("https://graph.facebook.com/v2.6/" + str(facebook_id) + "?fields=first_name&access_token=" + PAGE_ACCESS_TOKEN)
        
        dashboard_url = "http://jarvis-chatbot.herokuapp.com/" + facebook_id

        element = {"title": "Hi " + r.json()["first_name"] + ", nice to meet you!"}
        element["subtitle"] = "Set me up by visiting the Jarvis Dashboard."
        element["item_url"] = dashboard_url
        element["image_url"] = "https://easilydo.files.wordpress.com/2014/03/ownpersonalasst-bloggraphic.jpg"
        element["buttons"] = [{"type": "web_url", "url": dashboard_url, "title": "Set Up Accounts"}]

        sendCarouselMessage(facebook_id, [element])

    else:
        print payload
        parsed = json.loads(payload)
        print parsed['address']
        print parsed['title']
        if parsed['time'] is None:
            time = google_cal.now().isoformat()
            end_time = google_cal.minutes_later(30).isoformat()
        else:
            time = parsed['time']
            end_time = google_cal.minutes_later(time, 60)
        if parsed['person'] is None:
            emails = []
        google_cal.create_event(facebook_id, parsed['summary'],
                                parsed['address'], time, end_time, emails)
        sendTextMessage(facebook_id, "Putting this event into your calendar!")


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
