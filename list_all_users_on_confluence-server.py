#!/usr/bin/env python
import sys
import requests
from requests.auth import HTTPBasicAuth
import json
import yaml
import pdb
from pprint import pprint
from Confluence_apis import Confluence_server_api

# user help message
usage = f"Usage: python3 {sys.argv[0]} <atlassian server config yaml file> <atlassian cloud user file> <group filter list, comma separated>\n\nGroup filter list is a list of groups who's memebers will be excluded from the printed list, i.e. users you don't want to process.\n\nThe atlassian cloud user file is a csv file where the 3rd field is the users email (as the exported user list from arlassian web ui)."

# get the arguments
try:
    atlassian_server_config_filename = sys.argv[1]
except IndexError:
    print(f"{usage}\n\nERROR: Atlassian server config file argument missing")
    sys.exit()


try:
    atlassian_cloud_users_filename = sys.argv[2]
except IndexError:
    print(f"{usage}\n\nERROR: Atlassian cloud users file argument missing")
    sys.exit()


try:
   group_filter = sys.argv[3]
except IndexError:
    print(f"No group filter supplied, listing all users.")
    group_filter = None


# read the atlassian server config file
with open(atlassian_server_config_filename, 'r') as file:
    try:
        server_config = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        print(exc)

# read the atlassian cloud user file
cloud_users = set()
with open(atlassian_cloud_users_filename, 'r') as file:
    for line in file:
        cloud_users.add( line.split(",")[2].lower() )



# create confluence api instance
server = Confluence_server_api(server_config)

# get all users
server_users = server.get_users()
server_usernames = set( user['username'] for user in server_users )

# check if the user list should be filtered and exclude members of these groups
if group_filter:
    for group in group_filter.split(','):

        # get members of the filter group
        group_members = server.get_group_members(group)

        # remove these users from the set of usernames
        for member in group_members:
            server_usernames.discard(member['username'])
        



# fetch server email for users
server_emails = set()
for i,username in enumerate(server_usernames):

    print(f"{i}/{len(server_usernames)}")

    # get user info
    user = server.get_user_info(username)
    user_email = user['email'].lower()

    # keep the user if the email does not exists in the cloud
    if user_email not in cloud_users:
        server_emails.add(user_email)
        

print(f"Collected {len(server_emails)} new users from {len(server_usernames)} possible users.")






# get email for each user and print them in groups of n
n = 10
batch = []
print(f"{len(server_emails)} users in list, printing them in batches of {n}\n")
for i,user_email in enumerate(sorted(server_emails)):

    batch.append(user_email)


    # add a break every n lines
    if (i+1) % n == 0:
        print(f"{i+1}/{len(server_emails)}\n{','.join(batch)}\n")
        batch = []








