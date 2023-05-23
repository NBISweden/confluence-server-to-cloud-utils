#!/usr/bin/env python
import sys
import requests
from requests.auth import HTTPBasicAuth
import json
import yaml
import pdb
from pprint import pprint
import Confluence_apis
from Confluence_apis import name_processor
import time
import logging
from thefuzz import fuzz

# configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s\t[%(name)s.%(funcName)s:%(lineno)d] %(message)s",
    datefmt="%d/%b/%Y %H:%M:%S",                                                                                                                                 stream=sys.stdout)




# user help message
usage = f"Usage: python3 {sys.argv[0]} <atlassian config yaml file>"

# get the arguments
try:
    atlassian_config_filename = sys.argv[1]
except IndexError:
    print(f"{usage}\n\nERROR: Atlassian config file argument missing.")
    sys.exit()



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
users = confluence.get_users()
normalized_usernames = [ name_processor(user['user']['displayName']) for user in users ]

#pdb.set_trace()

# rename all spaces in list
c = 0
for i,space in enumerate(spaces):

    # skip not personal spaces
    if space['type'] != 'personal':
        continue

    # check if space name could be a personal space
    for username in normalized_usernames:
        ratio = fuzz.ratio(username, space['name'])
        if ratio >= 75:
            print(f"{username}\t{space['name']}")

    
    c += 1

logging.info(f"Done, found {c} spaces.")
