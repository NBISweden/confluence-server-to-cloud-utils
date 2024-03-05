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
from pprint import pprint

# configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s\t[%(name)s.%(funcName)s:%(lineno)d] %(message)s",
    datefmt="%d/%b/%Y %H:%M:%S",                                                                                                                             
    stream=sys.stdout)


def name_processor(name):                                                       

    return name.lower().replace('.','').replace(' ','').replace('_','')



# user help message
usage = f"Usage: python3 {sys.argv[0]} <atlassian config yaml file> [<max number of space memberships>]"

# get the arguments
try:
    logging.debug("Fetching config filename.")
    atlassian_config_filename = sys.argv[1]
except IndexError:
    print(f"{usage}\n\nERROR: Atlassian config file argument missing")
    sys.exit()

try:
    logging.debug("Fetching space membership cutoff")
    space_membership_cutoff = int(sys.argv[2])
except IndexError:
    space_membership_cutoff = 1

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

# get list of possible guest users
possible_guest_user = confluence.find_possible_guest_users(n_spaces = space_membership_cutoff, ignore_personal_spaces = True)

# list of system users not to convert, created by looking at the user names only, could have missed some
user_filter_list = [
                    'migrate-confluence-f857a78c-1013-42da-afd4-a1665b46a76d',
                    'Atlassian Assist',
                    'Issue Checklist',
                    'Automation for Jira',
                    'Proforma Migrator',
                    'Jira Service Management Widget',
                    'Epics Map for Jira',
                    'GitHub (production)',
                    'Jira Outlook',
                    'Jira Spreadsheets',
                    'Microsoft Teams for Jira Cloud',
                    'Opsgenie Integration',
                    'Statuspage for Jira',
                    'Slack',
                    'Trello',
                    'Zendesk Support for Jira',
                    'Atlas for Jira Cloud',
                   ]

found_users = 0
for user_id, user_perm in possible_guest_user.items():


    # skip users that are to be filtered out
    if user_perm['user']['displayName'] in user_filter_list:
        continue
    # skip app users
    if user_perm['user']['accountType'] == 'app':
        continue

    # increase the counter
    found_users += 1

    # get user's group memberships
    #user_group_memberships = confluence.get_user_group_memberships(user_id)
    #user_group_memberships_names = [group['name'] for group in user_group_memberships]

    # debug
    #user_group_memberships_names = []
    #pdb.set_trace()

    # get names of spaces the user has access to

    # print user entry
    print(f"{user_perm['user'].get('displayName')}\t{len(user_perm['spaces'])}\t{','.join([ space['name'] for space in user_perm['spaces'].values() ])}")


logging.info(f"Found {found_users} users that are members of {space_membership_cutoff} or less spaces.")




