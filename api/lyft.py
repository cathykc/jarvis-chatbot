import requests
from requests.auth import HTTPBasicAuth

# Returns (access token, refresh token)
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
   
# Sends request to get the lyft data
def get_ride_history_json(access_token, refresh_token):
    # Ride history constraints
    ride_history_start_date = '2016-04-01T21:04:22Z'
    ride_history_end_date = '2016-07-05T21:04:22Z'
    limit = 50

    # Request Lyft API with access token to get ride history
    ride_history_url = 'https://api.lyft.com/v1/rides?start_time=' + ride_history_start_date + '&end_time=' + ride_history_end_date + '&limit=' + str(limit)
    head = {"Authorization":"Bearer " + access_token}
    ride_history_request = requests.get(ride_history_url, headers=head)

    return ride_history_request.json()

    
# Performs analysis of lyft data to determine signal
def analyze(access_token, refresh_token):
    # Retrieve json
    json = get_ride_history_json(access_token, refresh_token)

    # Signals we want to get:
    go_to_work_time = 0
    home_address = 0
    home_lat = 0
    home_long = 0
    go_home_time = 0
    work_lat = 0
    work_long = 0

    # Analyze
    ride_list = []
    general_freq = {}
    morning_dropoff_freq = {}
    night_dropoff_freq = {}
    morning_pickup_freq = {}

    rides_list_json = json['ride_history']
    for ride in rides_list_json:
        # Get basic metadata about the ride
        pickup_address = ride['origin']['address'] if 'origin' in ride else None
        pickup_lat = ride['origin']['lat'] if 'origin' in ride else None
        pickup_long = ride['origin']['lng'] if 'origin' in ride else None

        dropoff_address = ride['destination']['address'] if 'destination' in ride else None
        dropoff_lat = ride['destination']['lat'] if 'destination' in ride else None
        dropoff_long = ride['destination']['lng'] if 'destination' in ride else None

        price = ride['price']['amount']
        requested_time = ride['requested_at'] 
        pickup_time = ride['pickup']['time'] if 'pickup' in ride else -1
        dropoff_time = ride['dropoff']['time'] if 'dropoff' in ride else -1

        # Add to ride list
        if dropoff_address is not None and pickup_address is not None:
            obj = {
                'pickup_address' : pickup_address,
                'dropoff_address' : dropoff_address,
                'pickup_lat' : pickup_lat,
                'pickup_long' : pickup_long,
                'dropoff_lat' : dropoff_lat,
                'dropoff_long' : dropoff_long,
                'requested_time' : requested_time,
                'pickup_time' : pickup_time,
                'dropoff_time' : dropoff_time
            }
            ride_list.append(obj)

        # Most frequent rides
        if pickup_address is not None:
            if pickup_address not in general_freq:
                loc_data = {
                    'address' : pickup_address,
                    'lat' : pickup_lat,
                    'long' : pickup_long,
                    'freq' : 1
                }
                general_freq[pickup_address] = loc_data
            else:
                general_freq[pickup_address]['freq'] += 1

        if dropoff_address is not None:
            if dropoff_address not in general_freq:
                loc_data = {
                    'address' : dropoff_address,
                    'lat' : dropoff_lat,
                    'long' : dropoff_long,
                    'freq' : 1
                }   
                general_freq[dropoff_address] = loc_data
            else:
                general_freq[dropoff_address]['freq'] += 1

    # Determine most popular pickup/dropoff
    max_count = 0
    max_count_address = ''
    second_count = 0
    second_count_address = ''
    
    for key in general_freq:
        address = general_freq[key]
        if address['freq'] > max_count:
            second_count = max_count
            second_count_address = max_count_address
            max_count = address['freq']
            max_count_address = address['address']
        elif address['freq'] > second_count:
            second_count = address['freq']
            second_count_address = address['address']


    home_address = max_count_address # ASSUMPTION
    work_address = second_count_address # ASSUMPTION
    home_lat = general_freq[home_address]['lat']
    home_long = general_freq[home_address]['long']

    # Most frequent pickup in morning

    # Most frequent destination at night

    # Most frequent destination in the morning

    #

    # Count most popular locations


    return (go_home_time,
            home_address,
            home_lat,
            home_long,
            go_to_work_time,
            work_address,
            work_lat,
            work_long)

def send_lyft_message():
    a = 1