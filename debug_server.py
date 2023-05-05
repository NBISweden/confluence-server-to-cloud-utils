
#!/usr/bin/env python
import sys
import requests
from requests.auth import HTTPBasicAuth
import json
import yaml
import pdb
from pprint import pprint
from Confluence_apis import Confluence_server_api
import logging

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
    print(f"{usage}\n\nERROR: Atlassian config file argument missing")
    sys.exit()



# read the atlassian config file
with open(atlassian_config_filename, 'r') as file:
    try:
        config = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        print(exc)


# create confluence api instance
c = Confluence_server_api(config)

group_name = 'confluence-users'
group_users = c.get_group_members(group_name)

# write all groups users to file
with open(f'{group_name}.members.tsv', 'w', encoding='utf-8') as group_file:
    for user in group_users:
        group_file.write(f'{user["username"]}\t{user["displayName"]}\n')

pdb.set_trace()
