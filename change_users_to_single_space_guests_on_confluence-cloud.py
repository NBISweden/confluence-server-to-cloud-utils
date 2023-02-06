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
usage = f"Usage: python3 {sys.argv[0]} <atlassian config yaml file>"

# get the arguments
try:
    logging.debug("Fetching config filename.")
    atlassian_config_filename = sys.argv[1]
except IndexError:
    print(f"{usage}\n\nERROR: Atlassian config file argument missing")
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

# request a list of all spaces
logging.info("Fetching spaces.")
#spaces = confluence.get_spaces(expand="permissions", paginate=False)
spaces = confluence.get_spaces(expand="permissions")
#spaces = []

# init
user_permissions = {}
group_permissions = {}

## Get all user-space and group-space  memberships
# go through all spaces
logging.info("Parsing permissions.")
for space in spaces:
    #continue
    logging.debug(f"Space: {space['name']}")

    # go through all permissions
    for permission in space['permissions']:

        # skip empty permissions
        if 'subjects' not in permission.keys():
            continue

        # if it is a user permission
        if permission['subjects'].get('user'):

            # for all users with permission
            for user in permission['subjects']['user']['results']:
                
                # save the user and space info
                try:
                    logging.debug(f"User: {user['accountId']}")
                    user_permissions[user['accountId']]['spaces'][space['key']] = space
                except KeyError:
                    # if it is the first time seeing this user
                    user_permissions[user['accountId']] = {}
                    user_permissions[user['accountId']]['spaces'] = {space['key']:space}
                    user_permissions[user['accountId']]['user'] = user

        # if it is a user permission
        elif permission['subjects'].get('group'):

            # for all groups with permission
            for group in permission['subjects']['group']['results']:
                
                # save the user and space info
                try:
                    logging.debug(f"Group: {group['id']}")
                    group_permissions[group['id']]['spaces'][space['key']] = space
                except KeyError:
                    # if it is the first time seeing this group
                    group_permissions[group['id']] = {}
                    group_permissions[group['id']]['spaces'] = {space['key']:space}
                    group_permissions[group['id']]['group'] = group

logging.debug("Parsing permissions finished.")


## get a complete list of all users
logging.info("Fetching all users from API.")
#users = confluence.get_users(paginate=False)
users = confluence.get_users()

#pdb.set_trace()

# add all users to user_permissions dict
for user in users:

    # find missing users
    if user['user']['accountId'] not in user_permissions:

        # initiate entry
        user_permissions[user['user']['accountId']] = {'spaces':{}, 'user':user['user']}


# get all groups
logging.info(f"Fetching groups.")
groups = confluence.get_groups()

# for each groups, get members
for group in groups:

    # fetch group members
    logging.info(f"Fetching group memebers from {group['name']}")
    members = confluence.get_group_members(group_id=group['id'])

    # initiate entry if group is missing in group_permissions
    if group['id'] not in group_permissions:
        group_permissions[group['id']] = {'spaces':{}, 'group':group}

    # skip groups with no permissions

    # for each member, add the groups spaces to the users spaces list
    for member in members:

        # initiate entry if member is missing in member_permissions
        if member['accountId'] not in user_permissions:

            # initiate entry
            user_permissions[member['accountId']] = {'spaces':{}, 'user':member}

        # add group spaces to user spaces
        user_permissions[member['accountId']]['spaces'].update(group_permissions[group['id']]['spaces'])
        


logging.info("Getting guest group id.")
# get guest group name
guest_group_id = ""
for group in groups:
    if group['name'].startswith("confluence-guests-"):
        guest_group_id = group['id']
if guest_group_id == "":
    print("Guest group id not found.")
    pdb.set_trace()


# make a lookup table for space keys to space names for easy access
key_to_name = { space['key']:space['name'] for space in spaces}

logging.info("Findinig users with only 1 space.")
c=0
# find users with access to only 1 space
for user_id,up in user_permissions.items():
    if len(user_permissions[user_id]['spaces']) <= 1:

        # count number of 1 space users
        c += 1

        # convert user to guest user
        logging.info(f"Converting {user_permissions[user_id]['user']['displayName']} to guest user with access to {key_to_name[list(user_permissions[user_id]['spaces'].keys())[0]]}")
        confluence.convert_to_guest_user(user_id, guest_group_id)


logging.info(f"Finished converting {c} users to guest users, out of {len(user_permissions)} total users.")




