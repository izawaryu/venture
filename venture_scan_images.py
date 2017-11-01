# Ryu Izawa
# Written 2017-10-26
# Last updated 2017-10-31


import csv
import string
import shutil
import os.path
import pandas as pd
import streetview as sv
from os import listdir
from os.path import isfile, join



def scan_images_for_species(genus_species, threshold):

    if not os.path.exists('./'+genus_species+'/'):
        os.makedirs('./'+genus_species+'/')

    if not os.path.exists('./Insufficient Detail/'):
        os.makedirs('./Insufficient Detail/')

    # Create the dataframe of images potentially containing the species.
    #obs = pd.DataFrame(columns=['pano', 'latitude', 'longitude', 'heading', 'confidence'])
    #G_S = genus_species.split()
    #obs.to_csv('./' + genus_species + '/' + '_'.join(G_S) + '.csv', index=False)

    images = [img for img in listdir('./Venture Images/') if isfile(join('./Venture Images/', img))]

    for img in images:

        #print img
        confidence = sv.suspected_presence(genus_species, './Venture Images/'+img)

        if confidence > threshold:
            shutil.move('./Venture Images/'+img, './{}/conf.{:.2f}_{}'.format(genus_species, confidence, img))
            print('{}: {} *** {}%'.format(string.capwords(genus_species), img, str(round(confidence*100,2))))

        else:
            shutil.move('./Venture Images/'+img, './Insufficient Detail/'+img)
            print 'Insufficient Detail: ' + img




scan_images_for_species('ailanthus altissima', 0.2)
