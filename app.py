from flask import Flask, request
import json
import requests
app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello World!"

APP_SECRET = "763bc897c7ab402b870ad33a7cd59062"
VALIDATION_TOKEN = "jarvis"
PAGE_ACCESS_TOKEN = "EAANTFr9A1IEBAFi3QsRXDkZBl5yVYZC5XrCuqUxZCXDcc2Y9rD3LEqAtdqhpNHZAfZAWUVCzh9XmZCKcTV3ZBPIuH4ChfqfYaIkha2zLsazbyxoB8vJKFwr0qbwtwO7lbZBsiOgXfGjKq5zTmJvKrmnxKYqkmZCRZAnv1XKqlZCK4cnEQZDZD"


@app.route("/webhook", methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        print "post called"
        try:
            print "post method"
            data = json.loads(request.data)
            for entry in data['entry']:
                for message in entry['messaging']:
                    if 'optin' in message:
                        pass
                    elif 'message' in message:
                        print "it's a message"
                        print "is message"
                        receivedMessage(message)
                    elif 'delivery' in message:
                        pass
                    elif 'postback' in message:
                        pass
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
            print "_-_________"
            return "Wrong Verify Token", 403


def receivedMessage(event):
    senderID = event['sender']['id']
    message = event['message']

    print senderID
    print message

    if 'text' in message:
        sendTextMessage(senderID, "Text received.")
    elif 'attachments' in message:
        sendTextMessage(senderID, "Attachment received.")


def sendTextMessage(recipientId, messageText):

    messageData = {}
    messageData['recipient'] = {'id': recipientId}
    messageData['message'] = {'text': messageText}

    callSendAPI(messageData)


def callSendAPI(messageData):
    r = requests.post(
        "https://graph.facebook.com/v2.6/me/messages/?access_token=" +
        PAGE_ACCESS_TOKEN,
        json=messageData
    )
    if r.status_code == 200:
        print "Successfully sent message."
    else:
        print "Unable to send message."


if __name__ == "__main__":
    app.run()
