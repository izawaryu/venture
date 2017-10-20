# Ryu Izawa
# Written 2017-10-15
# Last updated 2017-10-20

# 
# 
# 


import math
import json
import string
import random
import numpy as np
import pandas as pd
import urllib, urllib2
import tensorflow as tf


# Google Maps API Keys
key = "&key=" + 'AIzaSyA_phpapSMniXBO2AfGjxp3ZfAD64wyh1s'	# Verdi
#key = "&key=" + 'AIzaSyBXOIFAVM65wlaVsRjD-q6YnWQ4V0HpgZQ'	# Dreamfish
save_location = './'
Size = '448x448'
FoV = '15'
step_size = 0.0001
search_radius = 0.007
locations = []
locations_limit = 1000



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
        return [json_date, json_pano_id, json_latitude, json_longitude, 0]
    else:
        return None




def there_exists_a_new_pano_at(some_location):

    visited_pano_ids = [pano[1] for pano in locations]

    if some_location is not None and some_location[1] not in visited_pano_ids:
        return True
    else:
        return False




def distance_between_panos(first_pano, second_pano):

    scalar_distance = ((second_pano[2]-first_pano[2])**2 \
                      + (second_pano[3]-first_pano[3])**2) \
                      ** (1.0/2.0)

    return scalar_distance





def some_point_to_relative_bearing(observer_position, observer_track, relative_bearing):

    # Given an observer's position, observer's track and some measure of distance, 
    # return a pano in the direction of the relative bearing, the given distance away.
    # Return None if none exists.

    steps = 1
    new_point = None

    absolute_bearing = observer_track + relative_bearing
    lat_increment = math.sin(absolute_bearing)
    lon_increment = math.cos(absolute_bearing)

    while new_point is None:
        steps += 1
        if steps > 9:
            break

        latitude_of_the_new_point = observer_position[2] + (lat_increment * step_size * steps)
        longitude_of_the_new_point = observer_position[3] + (lon_increment * step_size * steps)
        coordinates_of_the_new_point = ('{},{}'.format(latitude_of_the_new_point, longitude_of_the_new_point))
        new_point = get_nearest_pano(coordinates_of_the_new_point)

        if there_exists_a_new_pano_at(new_point) and distance_between_panos(observer_position, new_point) < step_size:
            new_point = None

    return new_point




def continue_along_path(prior_point, current_point):

    lat_track = current_point[2] - prior_point[2]
    lon_track = current_point[3] - prior_point[3]
    current_track = np.arctan(lat_track / lon_track)

    # Do not iterate beyond the limiting number of locations.
    if len(locations) <= locations_limit:

        # Determine some point ahead of the current position and track.
        # 'Ahead' here means some distance away in an arbitrary direction, 
        # but not in reverse along the current track.

        # In this case, I'm checking all angles from fore to aft
        # along either side, in a fashion similar to breast stroke.
        # Angles are checked every pi/4 radians.
        # We do not consider checking panos in reverse.
        for relative_bearing in [math.pi * 0.0/6.0, \
                                 math.pi * 1.0/6.0, \
                                 math.pi * 11.0/6.0, \
                                 math.pi * 2.0/6.0, \
                                 math.pi * 10.0/6.0, \
                                 math.pi * 3.0/6.0, \
                                 math.pi * 9.0/6.0, \
                                 math.pi * 4.0/6.0, \
                                 math.pi * 8.0/6.0]:

            some_new_direction_of_travel = some_point_to_relative_bearing(current_point, current_track, relative_bearing)

            # If there is a new direction of travel (excluding reverse), follow it.
            if there_exists_a_new_pano_at(some_new_direction_of_travel) and \
                distance_between_panos(some_new_direction_of_travel, locations[0]) <= search_radius:

                print('{}: heading {:.1f} from {:.5f}, {:.5f}'.format(len(locations), math.degrees(current_track), some_new_direction_of_travel[2], some_new_direction_of_travel[3]))

                locations.append(some_new_direction_of_travel)
                df = pd.DataFrame(some_new_direction_of_travel).T
                df.to_csv('venture.csv', mode='a', header=False, index=False)

                # If the change in track is great enough, mark the spot as a possible intersection.
                if (relative_bearing/math.pi) in [(1.0/2.0), (3.0/2.0)]:
                    locations[-1][4] = 1

                if distance_between_panos(current_point, some_new_direction_of_travel) >= step_size:
                    continue_along_path(current_point, some_new_direction_of_travel)
                else:
                    continue_along_path(prior_point, some_new_direction_of_travel)

    return None




def venture_outward_from_location(latitude, longitude):

    # Starting at a given location,
    # move outward along paths of extisting GSV panoramas.

    coordinates = ('{},{}'.format(latitude, longitude))

    # Find the nearest panorama to the starting point, A.
    try:
        start_point = get_nearest_pano(coordinates)
    except ValueError:
        print('*** failure at venture_outward_from_location({})'.format(coordinates))

    # Find another nearby panorama, B.
    next_point = some_point_to_relative_bearing(start_point, 0.0, 0.0)

    locations.append(start_point)
    locations.append(next_point)

    continue_along_path(start_point, next_point)







# Apply some switch-like feature to toggle between starting a new locations list and not.
df = pd.DataFrame(locations, columns=['date', 'pano_id', 'latitude', 'longitude', 'comment'])
df_name = 'venture.csv'
df.to_csv(df_name, index=False)

#tail_point = pd.read_csv('venture.csv').tail(1)
#start_latitude = tail_point.iloc[0][2]
#start_longitude = tail_point.iloc[0][3]
#locations = pd.read_csv('venture.csv').values.tolist()

start_latitude = 40.246796
start_longitude = -74.064312

venture_outward_from_location(start_latitude, start_longitude)

