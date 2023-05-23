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
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


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


# create a browser
browser = webdriver.Chrome()

# login
browser.get(f"{config['url']}/wiki/login.action?os_destination=/spaces")
login_username = browser.find_element(By.ID, 'username')
login_username.send_keys(config['user'] + Keys.RETURN)
login_password = browser.find_element(By.ID, 'password')
login_password.send_keys(config['password'] + Keys.RETURN)
time.sleep(5)

# create confluence api instance
logging.debug("Creating confluence api object")
confluence = Confluence_cloud_api(config)

# get groups
groups = confluence.get_groups()

# find the guest group
guest_group_id = [ group['id'] for group in groups if group['name'].startswith('confluence-guests-') ][0]
users_group_id = [ group['id'] for group in groups if group['name'] == 'confluence-users' ][0]

# get the guest group members
users = confluence.get_group_members(guest_group_id)

# for each member, make sure they are not a member of the confluence-users group as well
for i,user in enumerate(users):

    # open the user's page
    browser.get(f"https://admin.atlassian.com/s/f857a78c-1013-42da-afd4-a1665b46a76d/users/{user['accountId']}")
    time.sleep(5)
    
    # find the toggle button
    browser.find_element(By.XPATH, f"//div[@data-test-id='user-details-toggle-{user['accountId']}']//span[@class='css-zg81aj']").click()
    time.sleep(1)

    #pdb.set_trace()

    #print(f"{user['publicName']}\t{user['accountId']}")

    #properties = confluence.get_user_properties(user['accountId'])






