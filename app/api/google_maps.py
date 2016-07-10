import googlemaps
from datetime import datetime
from app import User

gmaps = googlemaps.Client(key='AIzaSyCvMJ8qx_CXw2YF1A6LCGppfLB7BIBuJ30')

#returns a dict with text (String) and value (time in sec)

def driving_time_from_home(facebook_id, end):
    user = User.query.get(facebook_id)
    if user.lyft_home_lat is None or user.lyft_home_long is None:
        start = "525 Guerrero St"
    else:
        start = (user.lyft_home_lat, user.lyft_home_long)
    distance_matrix = gmaps.distance_matrix(
        start,
        end,
        mode="driving",
        units="imperial"
    )
    print distance_matrix
    print distance_matrix['rows'][0]['elements'][0]['duration']['text']
    return distance_matrix['rows'][0]['elements'][0]['duration']

def walking_time_from_home(facebook_id, end):
    user = User.query.get(facebook_id)
    if user.lyft_home_lat is None or user.lyft_home_long is None:
        start = "525 Guerrero St"
    else:
        start = (user.lyft_home_lat, user.lyft_home_long)
    print start
    distance_matrix = gmaps.distance_matrix(
        start,
        end,
        mode="walking",
        units="imperial"
    )
    print distance_matrix
    print distance_matrix['rows'][0]['elements'][0]['duration']['text']
    return distance_matrix['rows'][0]['elements'][0]['duration']

def driving_time_from_work(facebook_id, end):
    user = User.query.get(facebook_id)
    if user.lyft_work_lat is None or user.lyft_work_long is None:
        start = "1550 Bryant St"
    else:
        start = (user.lyft_work_lat, user.lyft_work_long)
    distance_matrix = gmaps.distance_matrix(
        start,
        end,
        mode="driving",
        units="imperial"
    )
    print distance_matrix
    print distance_matrix['rows'][0]['elements'][0]['duration']['text']
    return distance_matrix['rows'][0]['elements'][0]['duration']

def walking_time_from_work(facebook_id, end):
    user = User.query.get(facebook_id)
    if user.lyft_work_lat is None or user.lyft_work_long is None:
        start = "1550 Bryant St"
    else:
        start = (user.lyft_work_lat, user.lyft_work_long)
    distance_matrix = gmaps.distance_matrix(
        start,
        end,
        mode="walking",
        units="imperial"
    )
    print distance_matrix
    print distance_matrix['rows'][0]['elements'][0]['duration']['text']
    return distance_matrix['rows'][0]['elements'][0]['duration']
