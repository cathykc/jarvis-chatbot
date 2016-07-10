import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
from models import * 

# *****************************************************************************
#  LYFT SETUP / AUTH FUNCTIONS
# *****************************************************************************

# Lyft set up function called by app.py
def setup(request, facebook_id):
    # auth lyft
    (access_token, refresh_token) = authorize(request)

    # Get signal
    (go_home_time,
            home_address,
            home_lat,
            home_long,
            go_to_work_time,
            work_address,
            work_lat,
            work_long) = analyze(access_token, refresh_token)

    # Store all information in database
    store_signal_in_database(access_token, refresh_token, go_home_time,
            home_address,
            home_lat,
            home_long,
            go_to_work_time,
            work_address,
            work_lat,
            work_long, facebook_id)

    return "We think your home address is: <b>" + home_address + "</b> and your work address is <br>" + work_address + "</b>"

# Store signal retrieved into database
def store_signal_in_database(access_token, 
            refresh_token,
            go_home_time,
            home_address,
            home_lat,
            home_long,
            go_to_work_time,
            work_address,
            work_lat,
            work_long, facebook_id):

    user = User.query.get(facebook_id)
    if not user:
        return false

    user.lyft_access_token = access_token
    user.lyft_refresh_token = refresh_token
    user.lyft_go_home_time = go_home_time
    user.lyft_home_address = home_address
    user.lyft_home_lat = home_lat
    user.lyft_home_long = home_long
    user.lyft_go_work_time = go_work_time
    user.lyft_work_address = work_address
    user.lyft_work_lat = work_lat
    user.lyft_work_long = work_long

    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return false
    return true

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
    ride_history_start_date = '2016-06-01T21:04:22Z'
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

    rides_list_json = json['ride_history']
    for ride in rides_list_json:
        print 'retrieved'

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
        if dropoff_lat is not None and pickup_lat is not None:
            print 'adding'
            obj = {
                'pickup_address' : pickup_address,
                'dropoff_address' : dropoff_address,
                'pickup_lat' : round(pickup_lat,4),
                'pickup_long' : round(pickup_long,4),
                'dropoff_lat' : round(dropoff_lat,4),
                'dropoff_long' : round(dropoff_long,4),
                'requested_time' : requested_time,
                'pickup_time' : pickup_time,
                'dropoff_time' : dropoff_time
            }
            ride_list.append(obj)

        # # Most frequent rides
        # if pickup_address is not None:
        #     if pickup_address not in general_freq:
        #         loc_data = {
        #             'address' : pickup_address,
        #             'lat' : pickup_lat,
        #             'long' : pickup_long,
        #             'freq' : 1
        #         }
        #         general_freq[pickup_address] = loc_data
        #     else:
        #         general_freq[pickup_address]['freq'] += 1

        # if dropoff_address is not None:
        #     if dropoff_address not in general_freq:
        #         loc_data = {
        #             'address' : dropoff_address,
        #             'lat' : dropoff_lat,
        #             'long' : dropoff_long,
        #             'freq' : 1
        #         }   
        #         general_freq[dropoff_address] = loc_data
        #     else:
        #         general_freq[dropoff_address]['freq'] += 1


    # Determine home and work
    work_freq_counter = {}
    home_freq_counter = {}

    for ride in ride_list:
        requested_at = ride['requested_time']
        pickup_address = str(ride['pickup_lat']) + " " + str(ride['pickup_long'])
        dropoff_address = str(ride['dropoff_lat']) + " " + str(ride['dropoff_long'])

        # clean date
        clean_requested_at = rreplace(requested_at, ':', 1)
        clean_requested_at = clean_requested_at[:len(clean_requested_at)-5]
        clean_requested_at += 'UTC'
        print clean_requested_at

        date_object = datetime.strptime(clean_requested_at, '%Y-%m-%dT%H:%M:%S%Z')
        print date_object.hour 

        if date_object.hour > 13 and date_object.hour < 19:
            # morning pickup - home
            if pickup_address in home_freq_counter:
                home_freq_counter[pickup_address] += 1
            else:
                home_freq_counter[pickup_address] = 1

            #  morning dropoff - work
            if dropoff_address in work_freq_counter:
                work_freq_counter[dropoff_address] += 1
            else:
                work_freq_counter[dropoff_address] = 1

        elif date_object.hour > 22 and date_object.hour < 7:
             # night pickup - work
            if pickup_address in work_freq_counter:
                work_freq_counter[pickup_address] += 1
            else:
                work_freq_counter[pickup_address] = 1

            #  night dropoff - home
            if dropoff_address in home_freq_counter:
                home_freq_counter[dropoff_address] += 1
            else:
                home_freq_counter[dropoff_address] = 1

    # Determine home
    max_count = 0
    max_count_address = ''
    
    for key in home_freq_counter:
        count = home_freq_counter[key]
        print key + ' ' + str(count)
        if count > max_count:
            max_count = count
            max_count_address = key
    home_address = max_count_address 

    # Determine work
    max_count = 0
    max_count_address = ''
    
    for key in work_freq_counter:
        count = work_freq_counter[key]
        print key + ' ' + str(count)
        if count > max_count:
            max_count = count
            max_count_address = key
    work_address = max_count_address 

    print 'work'
    print work_address
    print 'home'
    print home_address

    work_lat = work_address.split(' ')[0]
    work_long = work_address.split(' ')[1]

    home_lat = home_address.split(' ')[0]
    home_long = home_address.split(' ')[1]



    return (go_home_time,
            home_address,
            home_lat,
            home_long,
            go_to_work_time,
            work_address,
            work_lat,
            work_long)


# *****************************************************************************
# HELPER METHODS
# *****************************************************************************
def rreplace(s, old, occurrence):
    li = s.rsplit(old, occurrence)
    return ''.join(li)

# *****************************************************************************
# LYFT RIDE REQUEST FUNCTIONS
# *****************************************************************************
def request_ride():
    a = 1

