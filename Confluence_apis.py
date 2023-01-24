import requests
from requests.auth import HTTPBasicAuth
import json
import pdb

class Confluence_server_api:
    """
    Class to interact with the Confluence Server API.
    """

    # create a object from a config file
    def __init__(self, config):

        self.user       = config['user']
        self.password   = config['password']
        self.baseurl    = config['url']
        self.auth       = HTTPBasicAuth(self.user, self.password)
        self.headers    = {
                            "Accept": "application/json",
                            "Content-Type": "application/json",
                          }


    def get_spaces(self, limit=1000, expand=None):
        """
        Returns a list of spaces, limited in number by {limit}. Expands properties listed comma-separated in {expand}.
        """

        # if there is anything to expand
        if expand:
            expand = f"&expand={expand}"
        else:
            expand = ''

        # define url and send request
        url = f"{self.baseurl}/rest/api/space?limit={limit}{expand}"

        return requests.request("GET", url, headers=self.headers, auth=self.auth).json()['results']


    def update_space_name(self, space_key, name):
        """
        Updates a space's name. Takes a space key string and a new name as a string as inputs.
        """
        
        # define url and payload, then send the request
        url = f"{self.baseurl}/rest/api/space/{space_key}"
        payload = "{'name': '" + name + "'}"

        return requests.put(url, data=payload, headers=self.headers, auth=self.auth).json()


#    def get_groups(self, limit=1000, expand=None):
#        """
#        Returns a list of groups, limited in number by {limit}. Expands properties listed comma-separated in {expand}.
#        """
#
#        if expand:
#            expand = f"&expand={expand}"
#        else:
#            expand = ''
#
#        # define url and send request
#        url = f"{self.baseurl}/rest/api/group?limit={limit}{expand}"
#        return requests.request("GET", url, headers=self.headers, auth=self.auth).json()['results']


#    def get_space_property(self, space_key, expand=None):
#        """
#        Returns properties of a space. Expands properties listed comma-separated in {expand}.
#        """
#
#        if expand:
#            expand = f"?expand={expand}"
#        else:
#            expand = ''
#
#        pdb.set_trace()
#        # define url and send request
#        url = f"{self.baseurl}/rest/api/space/{space_key}/property{expand}"
#        return requests.request("GET", url, headers=self.headers, auth=self.auth).json()['results']









class Confluence_cloud_api:
    """
    Class to interact with the Confluence Cloud API.
    """

    # create a object from a config file
    def __init__(self, config):

        self.user       = config['user']
        self.api_token  = config['api_token']
        self.baseurl    = config['url']
        self.auth       = HTTPBasicAuth(self.user, self.api_token)
        self.headers    = {
                            "Accept": "application/json",
                            "Content-Type": "application/json",
                          }


    def get_spaces(self, limit=10000, expand=None):
        """
        Returns a list of spaces, limited in number by {limit}. Expands properties listed comma-separated in {expand}.
        """

        # if there is anything to expand
        if expand:
            expand = f"&expand={expand}"
        else:
            expand = ''

        # define url and send request
        url = f"{self.baseurl}/wiki/rest/api/space?limit={limit}{expand}"

        pdb.set_trace()
        
        # fetch results
        response = requests.request("GET", url, headers=self.headers, auth=self.auth).json()

        # check if confluence limited the number of hits, seems to do that if you ask for expansions, setting it to 50
        if response['limit'] != limit:

            # save inital response
            results = response['results']

            # loop until all hits are collected
            i = 1
            while response['results'] and len(results) > limit:

                # ask for a new batch of results
                response = requests.request("GET", f"{url}&start={i * response['limit']}", headers=self.headers, auth=self.auth).json()

                # save the new batch together with the previous ones
                results += response['results']

                # increase counteults = response['results']
                i+=1

        else:
            # got them all in the first request
            results = response['results']

        # return at most the limit the user asked for
        return results[:limit]


















