#!/usr/bin/env python
import sys
import requests
from requests.auth import HTTPBasicAuth
import json
import yaml
import pdb
from pprint import pprint
import Confluence_apis
import time
import logging

# configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s\t[%(name)s.%(funcName)s:%(lineno)d] %(message)s",
    datefmt="%d/%b/%Y %H:%M:%S",                                                                                                                                 stream=sys.stdout)




# user help message
usage = f"Usage: python3 {sys.argv[0]} <atlassian config yaml file>  <label to add> [<space name filter (regex)>]"

# get the arguments
try:
    atlassian_config_filename = sys.argv[1]
except IndexError:
    print(f"{usage}\n\nERROR: Atlassian config file argument missing.")
    sys.exit()

try:
    label = sys.argv[2]
except IndexError:
    print(f"{usage}\n\nERROR: Label missing.")

try:
    name_filter = sys.argv[3]
except IndexError:
    print(f"WARNING: Space name filter missing, applying label to all spaces in Confluence instance.")
    name_filter = None
#    time.sleep(3)


# read the atlassian config file
with open(atlassian_config_filename, 'r') as file:
    try:
        config = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        print(exc)


# create confluence api instance
confluence = Confluence_apis.Confluence_cloud_api(config)

# request a list of all spaces
spaces = confluence.get_spaces()

# while testing, only rename the test space
#spaces = [ space for space in spaces if space['key'] == 'DAH' ]

# rename all spaces in list
c = 0
for i,space in enumerate(spaces):

    # if a filter is specified
    if name_filter:

        import re
        
        # check if filter does not match
        if not re.search(name_filter, space['name']):

            # skip if no match
            logging.debug(f"Skipping space {space['name']}, not matching name filter '{name_filter}'")
            continue


    logging.info(f"Adding label '{label}' to space '{space['name']}'")
    response = confluence.add_label_to_space(space['key'], label)
    #pdb.set_trace()
    
    # warn if something is wrong
    if not response.ok:
        logging.error(f"ERROR: Response code {response.status_code}, {response.text}")
    c += 1

logging.info(f"Done, added label {label} to {c} spaces.")
