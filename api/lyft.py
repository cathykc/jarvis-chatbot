import requests
from requests.auth import HTTPBasicAuth

# Returns access token and refresh token
def authorize(request):
    client_id = 'rFR4L19xgF5R'
    client_secret = 'pKzQ-w5cEypEPcxB2Ny6DHg2W1Ag1VUG'

    authorization_code = request.args.get('code')
    state = request.args.get('state')

    # Get access token
    oauth_url = 'https://api.lyft.com/oauth/token'
    r = requests.post(oauth_url, data = {'grant_type':'authorization_code', 'code':authorization_code}, auth=HTTPBasicAuth(client_id, client_secret));
    
    access_token = r.json()['access_token']
    refresh_token = r.json()['refresh_token']

    return (access_token, refresh_token)
   
def get_ride_history():
    # Use access token to get ride history
    ride_history_url = 'https://api.lyft.com/v1/rides?start_time=2016-01-01T21:04:22Z&end_time=2016-07-05T21:04:22Z&limit=50'
    head = {"Authorization":"Bearer " + access_token}
    r2 = requests.get(ride_history_url, headers=head)

    rides_list = r2.json()['ride_history']
    for ride in rides_list:
        pickup_address = ride['origin']['address']
        dropoff_address = ride['destination']['address']
        pickup_lat = ride['origin']['lat']
        pickup_long = ride['origin']['lng']
        dropoff_lat = ride['destination']['lat']
        dropoff_long = ride['destination']['lng']
        price = ride['price']['amount']

        requested_time = ride['requested_at']
        pickup_time = ride['pickup']['time'] if 'pickup' in ride else -1
        dropoff_time = ride['dropoff']['time'] if 'dropoff' in ride else -1

        print(pickup_address)