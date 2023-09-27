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
from collections import defaultdict

# configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s\t[%(name)s.%(funcName)s:%(lineno)d] %(message)s",
    datefmt="%d/%b/%Y %H:%M:%S",                                                                                                                             
    stream=sys.stdout)


# user help message
usage = f"""Usage% python3 {sys.argv[0]} <atlassian config yaml file> <old user_or_group1>%<new user_or_group1> [<old user_or_group2>%<old user_or_group2> ... <old user_or_group_N>%<old user_or_groupN>]
ex.
python3 {sys.argv[0]} config.ini old_username%new_username old.user@email.com%new.user@email.com old-user-id-1111-46d1-8e68-edc48151b41a%new-user-id-1111-46d1-8e68-edc48151b41a
or
python3 {sys.argv[0]} config.ini old_groupname%new_groupname old-group-id-1111-46d1-8e68-edc48151b41a%new-group-id-1111-46d1-8e68-edc48151b41a

Note:
It should work to transfer user permissions to groups and vice versa.
"""

# get the arguments
try:
    logging.debug("Fetching config filename.")
    atlassian_config_filename = sys.argv[1]
except IndexError:
    print(f"{usage}\n\nERROR: Atlassian config file argument missing")
    sys.exit()

logging.debug("Fetching transfer pairs")
transfer_pairs = sys.argv[2:]
if not transfer_pairs:
    print(f"{usage}\n\nERROR: No transfer pair(s) given")
    sys.exit()

# validate pair format
for pair in transfer_pairs:
    # split the pair
    try:
        old_entity, new_entity = pair.split('%')
    except:
        print(f"{usage}\n\nERROR: Malformatted transfer pair ({pair}). Should have format old%new where '%' is the separator between the old and new entity.")
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

# define a nested dict
nested_dict    = lambda: defaultdict(nested_dict)
permission_map = nested_dict()



## Get all user-space and group-space memberships
# go through all spaces
logging.info("Parsing permissions.")
for space in spaces:
    #continue
    logging.debug(f"Space: {space['name']}")

    # go through all permissions
    for permission in space['permissions']:

        # skip empty permissions
        if 'subjects' not in permission.keys():
            #pdb.set_trace()
            continue

        # for each subject with this permission
        for subject_type, subject in permission['subjects'].items():

            # skip metadata
            if subject_type == '_expandable':
                continue

            # for each entity of this subject_type
            for entity in subject['results']:

                # set the name of the id key depending on type
                id_key = 'accountId' if subject_type == 'user' else 'id'

                # init
                if entity[id_key] not in permission_map:
                    permission_map[entity[id_key]] = {'type':subject_type, 'spaces':{}}
                if space['id'] not in permission_map[entity[id_key]]['spaces']:
                    permission_map[entity[id_key]]['spaces'][space['id']] = []

                # save the permission
                permission_map[entity[id_key]]['spaces'][space['id']].append(permission['operation'])


# fetch all users and groups
users          = confluence.get_users()
groups         = confluence.get_groups()

# add missing users to the permission map
for user in users:
    # check if the user id is new
    if user['accountId'] not in permission_map:
        permission_map[user['accountId']] = {'type':'user', 'spaces':{}}


# add missing groups to the permission map
for group in groups:
    # check if the group id is new
    if group['id'] not in permission_map:
        permission_map[group['id']] = {'type':'group', 'spaces':{}}



# process each pair
for pair in transfer_pairs:

    # split the pair
    old_entity, new_entity = pair.split('%')


#    pdb.set_trace()

    # check if old entity is id or name
    if old_entity in permission_map:
        old_id = old_entity

    # if not, check if it is a user or group
    else:

        # init
        matches = []

        # find matching users
        matches += [ user['accountId'] for user in users if user['displayName'] == old_entity ]

        # find matching group
        matches += [ group['id'] for group in groups if group['name'] == old_entity ]

        if len(matches) > 1:
            logging.error(f"Fatal: multiple matching entities for name '{old_entity}'")
            sys.exit()
        elif len(matches) == 0:
            logging.error(f"Fatal: no matching entities for name '{old_entity}'")
            sys.exit()

        # there is only one match, get the id
        old_id = matches[0]



    # check if new entity is id or name
    if new_entity in permission_map:
        new_id = new_entity

    # if not, check if it is a user or group
    else:

        # init
        matches = []

        # find matching users
        matches += [ user['accountId'] for user in users if user['displayName'] == new_entity ]

        # find matching group
        matches += [ group['id'] for group in groups if group['name'] == new_entity ]

        if len(matches) > 1:
            logging.error(f"Fatal: multiple matching entities for name '{new_entity}'")
            sys.exit()
        elif len(matches) == 0:
            logging.error(f"Fatal: no matching entities for name '{new_entity}'")
            sys.exit()

        # there is only one match, get the id
        new_id = matches[0]

    
    # for each permission in the old, make so in the new
    old_permissions = permission_map[old_id]
    new_permissions = permission_map[new_id]

    
    # apply the old permissions to the new entity
    for space_id, permissions in old_permissions['spaces'].items():

        # get space info
        space      = [ space for space in spaces if space['id'] == space_id][0]
        space_key  = space['key']
        space_name = space['name']

#        if space_key != '~tsadmin':
#            continue
#        else:
#            pdb.set_trace()

        # create human read#ablm permission string
        permission_str = ", ".join(['read-space'] + [ f"{p['operation']}-{p['targetType']}" for p in permissions ]) 
        logging.info(f"Adding following permissions to {new_entity} on space '{space_name}': {permission_str}")

        # check if the new entity has read access to the space, as this is needed to set any other permission
        space_read_permission = {'operation': 'read', 'targetType': 'space'}
        if space_read_permission not in new_permissions['spaces'].get(space_id, []):
            # add space read permission
            confluence.add_permission_to_space(space_key, new_permissions['type'], new_id, 'space', 'read')


        for permission in permissions:

            # check if the new entity already have the old permission
            if permission in new_permissions['spaces'].get(space_id, []):
                continue



            # add the permission to the new entity
            logging.debug(f"Setting {permission} for {new_entity} on space {space_key}")
            confluence.add_permission_to_space(space_key, new_permissions['type'], new_id, permission['targetType'], permission['operation'])
    













































