# Ryu Izawa
# Written 2017-10-26
# Last updated 2017-10-30


import csv
import math
import json
import string
import random
import os.path
import numpy as np
import pandas as pd
import urllib, urllib2
import streetview as sv


# Google Maps API Keys
key = "&key=" + 'AIzaSyA_phpapSMniXBO2AfGjxp3ZfAD64wyh1s'	# Verdi
#key = "&key=" + 'AIzaSyBXOIFAVM65wlaVsRjD-q6YnWQ4V0HpgZQ'	# Dreamfish
Size = '448x448'
FoV = '35'
pano_limit = 22000




def retrieve_venture_imagery():

    # Open venture.csv file.
    if os.path.isfile('./venture.csv'):
        with open('./venture.csv', 'rb') as v:
            reader = csv.reader(v)
            locations = list(reader)

    # Step through list, querying Street View API for each pano
    # at angles orthogonal to the direction stored in 'comment'.
    for pano in locations[1:pano_limit]:

        left_view_heading = str((int(float(pano[4])) - 90 + 360)%360)
        left_pano_confidence = get_image_for_location(pano[1], left_view_heading)
        print('saved pano.{}_hdg.{}.jpg'.format(pano[1], left_view_heading))

        right_view_heading = str((int(float(pano[4])) + 90 + 360)%360)
        right_pano_confidence = get_image_for_location(pano[1], right_view_heading)
        print('saved pano.{}_hdg.{}.jpg'.format(pano[1], right_view_heading))



def get_image_for_location(pano, heading):

    base = "https://maps.googleapis.com/maps/api/streetview?"
    arg_size = 'size=' + Size
    arg_pano = '&pano=' + pano
    arg_FoV = '&fov=' + FoV
    arg_heading = '&heading=' + heading
    full_URL = base + arg_size + arg_pano + arg_FoV + arg_heading + key

    img_name = 'pano.'+pano + '_hdg.' + heading + '.jpg'
    urllib.urlretrieve(full_URL, os.path.join('./Venture Images/', img_name))




retrieve_venture_imagery()


