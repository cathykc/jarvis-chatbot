from yelp.client import Client
from yelp.oauth1_authenticator import Oauth1Authenticator

auth = Oauth1Authenticator(
    consumer_key='ymPqst4K4Monsi6pKrKRIw',
    consumer_secret='oDMh17eOwjb1HEmako1niyylUU8',
    token='lvyPIOu5PF9kG4uPvXEj-KXBgZA88qW8',
    token_secret='ypx32lfzyo7mNNomY-7m5U5qIhg'
)

client = Client(auth)


# prints the number of relevant results in that location
def get_top_locations(type, number, location):
    locations = []
    params = {
        'term': type,
        'limit': number
    }
    response = client.search(location, **params)
    for business in response.businesses:
        print "hello business"
        # name = business.name
        # locations[name] = business.location.display_address
        message = {}
        message["title"] = business.name
        message["subtitle"] = business.snippet_text
        message["item_url"] = business.url
        message["image_url"] = business.snippet_image_url

        buttons = [{"type": "postback", "title" : "Call Postback", "payload"
                    : "payload for yelp homies"}]
        message["buttons"] = buttons
        locations.append(message)
        print "lalaa locations"
    return locations

