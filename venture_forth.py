# Ryu Izawa
# Written 2017-10-15
# Last updated 2017-11-04


import csv
import math
import json
import string
import random
import os.path
import numpy as np
import pandas as pd
import urllib, urllib2



start_latitude = 40.355606
start_longitude = -74.027081



# Google Maps API Keys
key = "&key=" + 'AIzaSyA_phpapSMniXBO2AfGjxp3ZfAD64wyh1s'	# Verdi
#key = "&key=" + 'AIzaSyBXOIFAVM65wlaVsRjD-q6YnWQ4V0HpgZQ'	# Dreamfish
step_size = 0.0001
search_radius = 0.0500
locations_limit = 100000
trail = []
forks = []




def get_nearest_pano(coord):

    base = "https://maps.googleapis.com/maps/api/streetview/metadata?"
    arg_location = 'location=' + coord
    arg_heading = '&heading=' + '0'
    full_URL = base + arg_location + arg_heading + key

    req = urllib2.urlopen(full_URL)
    reply = req.read()
    json_parsed = json.loads(reply)
    json_status = json_parsed['status']

    if (json_status=='OK'):
        json_date = json_parsed['date']
        json_pano_id = json_parsed['pano_id']
        json_latitude = json_parsed['location']['lat']
        json_longitude = json_parsed['location']['lng']
        return (json_date, json_pano_id, json_latitude, json_longitude, 0.0)
    else:
        return None





def there_exists_a_new_pano(some_location):

    global trail

    visited_panos = [pano[1] for pano in trail]

    return not some_location[1] in visited_panos





def distance_between_panos(first_pano, second_pano):

    if second_pano is not None and first_pano is not None:
        scalar_distance = ((second_pano[2]-first_pano[2])**2 \
                          + (second_pano[3]-first_pano[3])**2) \
                          ** (1.0/2.0)
    else:
        scalar_distance = 1

    return scalar_distance





def some_point_to_relative_bearing(observer_position, observer_track, relative_bearing):

    # Given an observer's position, observer's track and some measure of distance, 
    # return a pano in the direction of the relative bearing, the given distance away.
    # Return None if none exists.

    steps = 0
    new_point = None

    absolute_bearing = observer_track + relative_bearing
    lat_increment = math.sin(absolute_bearing)
    lon_increment = math.cos(absolute_bearing)

    while new_point is None:
        steps += 1
        if steps > 3:
            break

        latitude_of_the_new_point = observer_position[2] + (lat_increment * step_size * steps)
        longitude_of_the_new_point = observer_position[3] + (lon_increment * step_size * steps)
        coordinates_of_the_new_point = ('{},{}'.format(latitude_of_the_new_point, longitude_of_the_new_point))
        np = get_nearest_pano(coordinates_of_the_new_point)

        # Record the direction of travel.
        if np is not None:
            new_point = (np[0], np[1], np[2], np[3], math.degrees(observer_track))

        if distance_between_panos(observer_position, new_point) < step_size/2.0:
            new_point = None

    return new_point





def next_step(current_point, current_track):

    global forks
    paths = set()
    next_step = None

    for relative_bearing in [math.pi * 2 * (3.0/4.0),
                             math.pi * 2 * (2.0/4.0),
                             math.pi * 2 * (1.0/4.0),
                             math.pi * 2 * (0.0/4.0)]:

        potential_next_step = some_point_to_relative_bearing(current_point, current_track, relative_bearing)

        if potential_next_step:
            paths.add(potential_next_step)

    for path in paths:
        if there_exists_a_new_pano(path):
            forks.append(path)
            forks.append(current_point)

    if forks:
        forks.pop()
        return forks.pop()
    else:
        return None





def travel_along_path(prior_point, current_point):

    # When working with this trig, consider '0' often runs horizontally
    # to the right in a conventional cartesian grid, with angles increasing counter-clockwise.
    # We're using an absolute lat/lon grid, so '0' is geo-north and angles increase clockwise.
    lat_track = current_point[2] - prior_point[2]
    lon_track = current_point[3] - prior_point[3]
    current_track = (math.atan2(lon_track,lat_track)+2*math.pi)%(2*math.pi)

    way_ahead = next_step(current_point, current_track)

    if distance_between_panos(start_point, way_ahead) < search_radius:
        new_prior_point = current_point
        new_current_point = way_ahead
    else:
        new_prior_point = forks.pop()
        new_current_point = forks.pop()

    return new_prior_point, new_current_point








def venture_forth(latitude, longitude):

    # Starting at a given location,
    # move outward along paths of extisting GSV panoramas.

    global trail
    global start_point

    if os.path.isfile('./venture.csv'):
        with open('venture.csv', 'rb') as v:
            reader = csv.reader(v)
            trail = list(reader)
            latitude = trail[-1][2]
            longitude = trail[-1][3]
    else:
        df = pd.DataFrame(trail, columns=['date', 'pano_id', 'latitude', 'longitude', 'comment'])
        df.to_csv('venture.csv', index=False)

    coordinates = ('{},{}'.format(latitude, longitude))

    try:
        start_point = last_point = get_nearest_pano(coordinates)
        next_point = this_point = next_step(start_point, 0.0)
    except:
        print '*** No pano found at starting point ***'

    trail.append(start_point)
    sp = pd.DataFrame(list(start_point)).T
    sp.to_csv('venture.csv', mode='a', header=False, index=False)

    trail.append(next_point)
    np = pd.DataFrame(list(next_point)).T
    np.to_csv('venture.csv', mode='a', header=False, index=False)

    while len(trail) <= locations_limit:

        last_point, this_point = travel_along_path(last_point, this_point)
        trail.append(this_point)

        df = pd.DataFrame(list(this_point)).T
        df.to_csv('venture.csv', mode='a', header=False, index=False)
        print('{}: {:.4f} ; {:.4f} heading {:3.0f}  {}'.format(len(trail), this_point[2], this_point[3], this_point[4], this_point[1]))

    print [pt[1] for pt in forks]
    print '*** DONE VENTURING ***'





venture_forth(start_latitude, start_longitude)

