#!/usr/bin/env python
import sys
import requests
from requests.auth import HTTPBasicAuth
import json
import yaml
import pdb
from pprint import pprint


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


# define a confluence class
class Confluence:

    # create a object from a config file
    def __init__(self, config):

        self.user       = config['user']
        self.password   = config['password']
#        self.api_token  = config['api_token'] # api tokens only supported in cloud api :/
        self.baseurl    = config['url']
        self.auth       = HTTPBasicAuth(self.user, self.password)
        self.headers    = {
                        "Accept": "application/json",
                        "Content-Type": "application/json",
#                        "Authorization": f"Bearer {self.api_token}"
                        }


    def get_spaces(self, limit=1000):
        """
        Returns a list of spaces, limited in number by {limit}.
        """

        # define url and send request
        url = f"{self.baseurl}/rest/api/space?limit={limit}"
        return requests.request("GET", url, headers=self.headers, auth=self.auth).json()['results']


    def update_space_name(self, space_key, name):
        """
        Updates a space's name. Takes a space key string and a new name as a string as inputs.
        """
        
        # define url and payload, then send the request
        url = f"{self.baseurl}/rest/api/space/{space_key}"
        payload = "{'name': '" + name + "'}"
        return requests.put(url, data=payload, headers=self.headers, auth=self.auth).json()




# create confluence api instance
confluence = Confluence(config)

# request a list of all spaces
spaces = confluence.get_spaces()

# while testing, only rename the test space
spaces = [ space for space in spaces if space['key'] == 'DAH' ]

# rename all spaces in list
for i,space in enumerate(spaces):
    print(f"Renaming {i+1}/{len(spaces)}:\t{space['name']} -> {prefix}{space['name']}")
    confluence.update_space_name(space['key'], f"{prefix}{space['name']}")

print("Done")
