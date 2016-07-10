# This mesasge sends a Lyft deeplink CTA to a recipient through messenger
def send_lyft_cta(fbid):
    buttonsList = [{
        "type" : "web_url",
        "url" : "http://jarvis-chatbot.herokuapp.com/lyft_request_ride",
        "title" : "Get a Lyft to Work"
    }]
    sendButtonMessage(recipientId, 'Need a ride to work?', buttonsList)

