from yelp.client import Client
from yelp.oauth1_authenticator import Oauth1Authenticator
import json

auth = Oauth1Authenticator(
    consumer_key='ymPqst4K4Monsi6pKrKRIw',
    consumer_secret='oDMh17eOwjb1HEmako1niyylUU8',
    token='lvyPIOu5PF9kG4uPvXEj-KXBgZA88qW8',
    token_secret='ypx32lfzyo7mNNomY-7m5U5qIhg'
)

client = Client(auth)


# prints the number of relevant results in that location
def get_top_locations(type, number, location, time, who):
    locations = []
    params = {
        'term': type,
        'limit': number
    }
    response = client.search(location, **params)
    for business in response.businesses:
        print location
        print type
        # print "hello business"
        # name = business.name
        # locations[name] = business.location.display_address
        payload = {}
        payload['title'] = business.name
        payload['address'] = business.location.display_address
        payload['time'] = time
        payload['person'] = who
        json_payload = json.dumps(payload)
        #count = 0
        #for person in who:
        #    payload['person' + count] = who[count]
        #    count += 1

        message = {}
        message["title"] = business.name
        message["subtitle"] = business.snippet_text
        message["item_url"] = business.url
        message["image_url"] = business.image_url

        buttons = [{"type": "postback", "title" : "Choose this location",
                    "payload"
                    : json_payload}]
        message["buttons"] = buttons
        locations.append(message)
    return locations

