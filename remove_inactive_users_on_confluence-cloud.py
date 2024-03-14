#!/usr/bin/env python
import sys
import requests
from requests.auth import HTTPBasicAuth
import json
import yaml
import pdb
from pprint import pprint
from Confluence_apis import Confluence_cloud_api
import logging

# configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s\t[%(name)s.%(funcName)s:%(lineno)d] %(message)s",
    datefmt="%d/%b/%Y %H:%M:%S",                                                                                                                             
    stream=sys.stdout)


# user help message
usage = f"Usage: python3 {sys.argv[0]} <atlassian config yaml file> <user id list>"

# get the arguments
try:
    logging.debug("Fetching config filename.")
    atlassian_config_filename = sys.argv[1]
except IndexError:
    print(f"{usage}\n\nERROR: Atlassian config file argument missing")
    sys.exit()

try:
    logging.debug("Fetching group filter list")
    user_id_list_file = sys.argv[2]
except IndexError:
    print(f"{usage}\n\nERROR: User id list argument missing")
    sys.exit()

# read the atlassian config file
logging.debug("Reading config file.")
with open(atlassian_config_filename, 'r') as file:
    try:
        config = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        print(exc)


# create confluence api instance
logging.debug("Creating confluence api object")
confluence = Confluence_cloud_api(config)

# get groups
groups = confluence.get_groups()

# find the guest group
guest_group_id = [ group['id'] for group in groups if group['name'].startswith('confluence-guests-') ][0]
users_group_id = [ group['id'] for group in groups if group['name'] == 'confluence-users' ][0]

# for each user in the list, remove them from the users group
with open(user_id_list_file, 'r') as file:
    user_ids = file.readlines()

for i,user_id in enumerate(user_ids):

    # remove leading and trailing white spaces
    user_id = user_id.strip()

    # skip empty lines
    if not user_id:
        continue

    # remove the user from the group
    response = confluence.remove_user_from_group(user_id, users_group_id)

    # check the response
    if response.status_code == 204:
        logging.info(f"{i+1}/{len(user_ids)}: User {user_id} removed from confluence-users group")
    else:
        logging.error(f"Failed to remove user {user_id} from confluence-users group")
        logging.error(response.text)

logging.info(f"Finished")




