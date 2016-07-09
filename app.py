from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, render_template, session
from api import google_cal, yelp_api, lyft
import json
import requests
import uuid
app = Flask(__name__)
app.secret_key = str(uuid.uuid4())

# *****************************************************************************
# DATABSASE AND MODELS
# *****************************************************************************

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    facebook_id = db.Column(db.Integer, unique=True)

    def __init__(self, facebook_id):
        self.facebook_id = facebook_id

    def __repr__(self):
        return str(self.facebook_id)

# *****************************************************************************
# WEBAPP ROUTES
# *****************************************************************************

@app.route("/")
@app.route("/<senderID>")
def dashboard(senderID=None):
    if senderID == None:
        return "Click in through Messenger"
    session['fbid'] = senderID
    return render_template('dashboard.html')

@app.route("/lyft_auth_redirect")
def lyft_auth():
    (access_token, refresh_token) = lyft.authorize(request)

    fbid = session['fbid']

    # Store access_token and refresh_token in db
    return "Got them for fbid: " + fbid 

@app.route("/google_auth")
def google_auth():
    return google_cal.oauth()

@app.route('/google_oauth2callback')
def google_oauth2callback():
    return google_cal.oauth2callback()

@app.route("/yelp_auth")
def yelp_auth():
    return "YELP AUTH"

# *****************************************************************************
# CHATBOT WEBHOOK
# *****************************************************************************

# please excuse pulic keys - to move soon
APP_SECRET = "763bc897c7ab402b870ad33a7cd59062"
VALIDATION_TOKEN = "jarvis"
PAGE_ACCESS_TOKEN = "EAANTFr9A1IEBAFi3QsRXDkZBl5yVYZC5XrCuqUxZCXDcc2Y9rD3LEqAtdqhpNHZAfZAWUVCzh9XmZCKcTV3ZBPIuH4ChfqfYaIkha2zLsazbyxoB8vJKFwr0qbwtwO7lbZBsiOgXfGjKq5zTmJvKrmnxKYqkmZCRZAnv1XKqlZCK4cnEQZDZD"


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
    senderID = event['sender']['id']
    message = event['message']

    print senderID
    print message

    if 'text' in message:
        # sendTextMessage(senderID, "Text received.")
        text = message["text"]

        if 'ping' in text:
             sendTextMessage(senderID, "pong")

        if "my events" in text:
            sendTextMessage(senderID, google_cal.events_today())

        # Schedule coffee in Mission with Mom
        elif 'coffee' in text:
            split = text.split()
            location = split[3]
            print "before entering yelp file"
            response = yelp_api.get_top_locations('coffee', 3, location)
            # to_user = ""
            # i = 1
            # for r in response:
            #     string = 'hi test test'
                # to_user += i + " " + r + "\n"
            print response
            sendTextMessage(senderID, "coffee")
        else:
            sendTextMessage(senderID, "Text received.")

    elif 'attachments' in message:
        sendTextMessage(senderID, "Attachment received.")

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
    senderID = event['sender']['id']
    sendTextMessage(senderID, "Postback called.")


# *****************************************************************************
# CHATBOT MESSAGES
# *****************************************************************************

# Send a text mesage.
def sendTextMessage(recipientId, messageText):

    messageData = {'recipient': {'id': recipientId}}
    messageData['message'] = {'text': messageText}
    
    print messageText
    callSendAPI(messageData)


# Send an image message.
def sendImageMessage(recipientId, imageUrl):
    messageData = {'recipient': {'id': recipientId}}

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
def sendButtonMessage(recipientId, messageText, buttonList):
    messageData = {"recipient": {"id": recipientId}}

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
def sendCarouselMessage(recipientId, elementList):
    messageData = {'recipient': {'id': recipientId}}

    attachment = {'type': "template"}
    attachment['payload'] = {'template_type': "generic",
                             'elements': elementList}
    messageData['message'] = {'attachment': attachment}

    callSendAPI(messageData)


def callSendAPI(messageData):
    print messageData
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


if __name__ == "__main__":
    app.run()
