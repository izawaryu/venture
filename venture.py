# Ryu Izawa
# Written 2017-10-15
# Last updated 2017-10-25


import math
import json
import string
import random
import numpy as np
import pandas as pd
import urllib, urllib2
import tensorflow as tf
import streetview as sv


# Google Maps API Keys
key = "&key=" + 'AIzaSyA_phpapSMniXBO2AfGjxp3ZfAD64wyh1s'	# Verdi
#key = "&key=" + 'AIzaSyBXOIFAVM65wlaVsRjD-q6YnWQ4V0HpgZQ'	# Dreamfish
save_location = './'
target = 'ailanthus altissima'
Size = '448x448'
step_size = 0.0001
search_radius = 0.02
locations = []
observations = []
locations_limit = 4500




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

        # Record the direction of travel.
        if new_point is not None:
            new_point[4] = math.degrees(observer_track)

        if there_exists_a_new_pano_at(new_point) and distance_between_panos(observer_position, new_point) < step_size:
            new_point = None

    return new_point




def continue_along_path(prior_point, current_point):

    lat_track = current_point[2] - prior_point[2]
    lon_track = current_point[3] - prior_point[3]
    # When working with this trig, consider '0' often runs horizontally
    # to the right in a conventional cartesian grid, with angles increasing counter-clockwise.
    # We're using an absolute lat/lon grid, so '0' is geo-north and angles increase clockwise.
    current_track = (math.atan2(lon_track,lat_track)+2*math.pi)%(2*math.pi)

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

                print('{}: travelling {:3.0f} from {:.4f}, {:.4f}'.format(len(locations), math.degrees(current_track), some_new_direction_of_travel[2], some_new_direction_of_travel[3]))

                locations.append(some_new_direction_of_travel)
                df = pd.DataFrame(some_new_direction_of_travel).T
                df.to_csv('venture.csv', mode='a', header=False, index=False)

                fore_view = int(round(math.degrees(current_track)))
                fore_left = (fore_view - 75 + 360)%360
                fore_right = (fore_view + 75 + 360)%360

                rear_view = (fore_view + 180)%360
                rear_left = (rear_view + 75 + 360)%360
                rear_right = (rear_view - 75 + 360)%360

                #examine_location(current_point[2], current_point[3], str(fore_view))
                examine_location(current_point[2], current_point[3], str(fore_left))
                examine_location(current_point[2], current_point[3], str(fore_right))

                #examine_location(current_point[2], current_point[3], str(rear_view))
                examine_location(current_point[2], current_point[3], str(rear_left))
                examine_location(current_point[2], current_point[3], str(rear_right))

                if distance_between_panos(current_point, some_new_direction_of_travel) >= step_size:
                    continue_along_path(current_point, some_new_direction_of_travel)
                else:
                    continue_along_path(prior_point, some_new_direction_of_travel)

    return None




def examine_location(lat, lon, hdg):
    # This function is used to test Google Street View images 
    # for some target object or species.
    # Each examination is added to the locations list 
    # with its coordinates, direction and 
    # the confidence level resulting from 
    # a run through a given CNN neural net.

    loc = '%.4f,%.4f' % (lat, lon)

    if sv.useable_view_exists(coord=loc, heading=hdg):
        in_view = sv.get_view(coord=loc, heading=hdg)
        confidence = sv.suspected_presence(target, in_view)

        if confidence > 0.01:
            print('{}:     facing {} from {:.4f}, {:.4f}  ***  {:.2f} {}'.format(len(locations), hdg, lat, lon, confidence, target))
            df = pd.DataFrame([lat, lon, hdg, confidence]).T
            df.to_csv(target_file, mode='a', header=False, index=False)

        return [lat, lon, hdg, confidence]

    else:
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







df = pd.DataFrame(locations, columns=['date', 'pano_id', 'latitude', 'longitude', 'comment'])
df_name = 'venture.csv'
df.to_csv(df_name, index=False)

target_frame = pd.DataFrame(locations, columns=['latitude', 'longitude', 'heading', 'confidence'])
target_name = target.split()
target_name.append('csv')
target_file = '.'.join(target_name)
target_frame.to_csv(target_file, index=False)


start_latitude = 40.366902
start_longitude = -74.067603

venture_outward_from_location(start_latitude, start_longitude)

