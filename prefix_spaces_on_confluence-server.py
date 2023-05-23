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
usage = f"Usage: python3 {sys.argv[0]} <atlassian config yaml file> <prefix to add to space names>"

# get the arguments
try:
    atlassian_config_filename = sys.argv[1]
except IndexError:
    print(f"{usage}\n\nERROR: Atlassian config file argument missing")
    sys.exit()

try:
    prefix = sys.argv[2]
except IndexError:
    print(f"{usage}\n\nERROR: Prefix argument missing")
    sys.exit()


# read the atlassian config file
with open(atlassian_config_filename, 'r') as file:
    try:
        config = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        print(exc)


# create confluence api instance
confluence = Confluence_server_api(config)

# request a list of all spaces
spaces = confluence.get_spaces()

# while testing, only rename the test space
# spaces = [ space for space in spaces if space['key'] == 'DAH' ]

# rename all spaces in list
for i,space in enumerate(spaces):

    # skip special spaces
    space_filter_list = [
                        ]
    if space['name'] in space_filter_list:
        print(f"Skipping {space['name']} due to space filter list.")
        continue

    print(f"Renaming {i+1}/{len(spaces)}:\t{space['name']} -> {prefix}{space['name']}")
    response = confluence.update_space_name(space['key'], f"{prefix}{space['name']}")
    #pdb.set_trace()

print("Done")
