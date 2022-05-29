#! /usr/bin/env python3

import re, os, json
from datetime import datetime

# root directory where "Photos from xxxx" sub-directories are found
directory = "/Users/ipirva/Downloads/Takeout/Google\xa0Photos"
photos_directory_name = "Photos from "

"""
Inside directory we expect to find folders like "Photos from xxxx", where xxxx is the year the photos where taken
Get inside each folder "Photos from xxxx" and look for pairs abc.json, abc.HEIC/.jpg or any other photo/video extentions
Different cases we have to consider (heic is just an example for photo and mp4 just an example for video extentions):
x.heic(1).json -> x(1).heic
x.mp4, x.heic -> x.heic.json
x-modifié.jpg -> x.jpg (modifié is french keyword, I do count for any word -xxx)

From each json file read photoTakenTime.timestamp and get the month and the year like 02_2022 for example for february 2022
Inside each "Photos from xxxx" create the needed month_year folders and move the right photos, videos, json files inside
Set accessed and modified times for each file to photoTakenTime.timestamp
"""

if not os.path.isdir(directory):
    exit(f"Please make sure that the directory {directory} exists.")

# ['Photos from 2015', 'Photos from 2012', 'Photos from 2011', 'Photos from 2016', 'Photos from 2020', 'Photos from 2018', 'Photos from 2019', 'Photos from 2021', 'Photos from 2017']
photos_directory = [ name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name)) and name.startswith(photos_directory_name) ]

if len(photos_directory) == 0:
    exit(f"No folder like {photos_directory_name} found in {directory}")

photos_directory_paths = sorted(os.path.join(directory, name) for name in photos_directory)
photos_directory_new = {}

for i in photos_directory_paths:
    files = [ name for name in os.listdir(i) if os.path.isfile(os.path.join(i, name))]
    json_files = [ os.path.join(i, name) for name in files if name.endswith(".json") ]
    non_json_files = [ os.path.join(i, name) for name in files if not name.endswith(".json") ]

    if len(json_files) != 0 and len(non_json_files) != 0:
        print(f"Found both json and non json files in {i}")
    
    for j in json_files:
        # j_ = j.rstrip(".json")
        # IMG_1830.HEIC.json will become IMG_1830
        j_ = re.sub(r'\..*', '', j)

        # handle names like x.heic(1).json which are for x(1).heic
        match_number = re.search('(\([0-9]{1,4}\))$', j.rstrip(".json"))
        match_number = match_number.group(1) if match_number else None

        if match_number:
            j_dirname = os.path.dirname(j)
            j_basename = os.path.basename(j)
    
            j_basename_split = j_basename.split('.')
            j_basename_split[0] = j_basename_split[0]+match_number

            j_basename = '.'.join(j_basename_split)

            j_new = os.path.join(j_dirname, j_basename).rstrip(".json").rstrip(match_number) # this may be IMG_0023(1).JPG
        
        if j.rstrip(".json") not in non_json_files and j_new in non_json_files:
            j_ = re.sub(r'\..*', '', j_new)

        if j.rstrip(".json") in non_json_files or j_new in non_json_files:
            with open(j, 'r') as f:
                j_dict = json.load(f)
            
            # cast string to int
            photo_timestamp_orig = j_dict['photoTakenTime']['timestamp']
            photo_timestamp = datetime.fromtimestamp(int(photo_timestamp_orig))
            photo_folder = os.path.join(str(i), photo_timestamp.strftime('%m_%Y'))

            if photo_folder not in photos_directory_new.keys():
                print(f"I found photos from month_year {photo_timestamp.strftime('%m_%Y')} in the folder {i}")
                photos_directory_new[photo_folder] = []

            photos_directory_new[photo_folder].append((j,int(photo_timestamp_orig)))
            
            j_search_regex = r''+re.escape(j_)+r'(?:-\w+\W+)?\..*$'
            j_search = re.compile(j_search_regex, re.UNICODE | re.IGNORECASE)
            j_filter = list(filter(j_search.match, non_json_files))

            if len(j_filter) != 0:
                for k in range(len(j_filter)):
                    photos_directory_new[photo_folder].append((j_filter[k], int(photo_timestamp_orig)))

for i in photos_directory_new.keys():
    if not os.path.isdir(i):
        os.mkdir(i)

    for j in photos_directory_new[i]:
        # file path, timestamp
        a, b = j
        print(f"Moving {a} to {os.path.join(i, os.path.basename(a))}")
        try:
            print(a)
            if os.path.isfile(a):
                os.rename(a, os.path.join(i, os.path.basename(a)))
                # modified and accessed time set to photo taken time
                os.utime(os.path.join(i, os.path.basename(a)), (b, b))
        except Exception as e:
            print(f"Error moving {a} to {os.path.join(i, os.path.basename(a))}")
            pass