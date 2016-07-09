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
    print "Entered the yelp function call"
    locations = {}
    params = {
        'term': type,
        'limit': number
    }
    print "Entering the API call"
    response = client.search(location, **params)
    print "made it through the API call"
    for business in response.businesses:
        name = business.name
        locations[name] = business.location.display_address
    return locations

