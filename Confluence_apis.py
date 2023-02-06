import requests
from requests.auth import HTTPBasicAuth
import json
import pdb
import logging
import re

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
        logging.debug(f"Fetching URL: {url}")

        return requests.request("GET", url, headers=self.headers, auth=self.auth).json()['results']


    def update_space_name(self, space_key, name):
        """
        Updates a space's name. Takes a space key string and a new name as a string as inputs.
        """
        
        # define url and payload, then send the request
        url = f"{self.baseurl}/rest/api/space/{space_key}"
        payload = "{'name': '" + name + "'}"

        logging.debug(f"Putting URL: {url}\tPayload: {payload}")

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





    def get(self, url, params=None, expand=None, limit=100, paginate=True):
        """
        Wrapper function to make API calls that will keep sending subsequent requests if the answer is paginated.
        """

        # if there is anything to expand
        if expand:
            expand = f"&expand={expand}"
        else:
            expand = ''

        # if there is a parameter dict
        if params:
            params_str = ""
            for key,val in params.items():
                params_str += f"&{str(key)}={str(val)}"
        else:
            params_str = ''

        # define url and send request
        request_url = f"{url}?limit={limit}{expand}{params_str}"
        logging.debug(f"Fetching URL: {request_url}")
        
        # fetch results
        response = requests.request("GET",
                                    request_url,
                                    headers=self.headers,
                                    auth=self.auth,
                                    ).json()

        # check if confluence limited the number of hits, seems to do that if you ask for expansions, setting it to 50
        #pdb.set_trace()
        if response['limit'] != limit and paginate:

            logging.debug(f"API pagination detected, continuing sending more requests.")

            # save inital response
            results = response['results']

            # loop until all hits are collected
            i = 1
            while response['results'] and len(results) <= limit:


                logging.debug(f"Fetching URL: {request_url}&start={i * response['limit']}")
                # ask for a new batch of results
                response = requests.request("GET",
                                            f"{request_url}&start={i * response['limit']}", 
                                            headers=self.headers,
                                            auth=self.auth,
                                            ).json()

                # save the new batch together with the previous ones
                results += response['results']

                # increase counteults = response['results']
                i+=1
            
            logging.debug("API pagination finished.")

        else:
            # got them all in the first request
            results = response['results']

        # return at most the limit the user asked for
        return results[:limit]


    def post(self, url, data=None, params=None):
        """
        Wrapper function to post data to the API.
        """
        #pdb.set_trace()
        return requests.request("POST", url, data=data, headers=self.headers, params=params, auth=self.auth,)



    def delete(self, url, data=None, params=None):
        """
        Wrapper function to delete data to the API.
        """
        #pdb.set_trace()
        return requests.request("DELETE", url, data=data, headers=self.headers, params=params, auth=self.auth,)




    def get_spaces(self, limit=10000, expand=None, paginate=True):
        """
        Returns a list of spaces, limited in number by {limit}. Expands properties listed comma-separated in {expand}.
        """
        # define url and send request
        return self.get(f"{self.baseurl}/wiki/rest/api/space", limit=limit, expand=expand, paginate=paginate)


    def get_users(self, limit=10000, expand=None, paginate=True):
        """
        Returns a list of users, limited in number by {limit}.
        """
        return self.get(f"{self.baseurl}/wiki/rest/api/search/user", params={"cql":"type=user"}, limit=limit, expand=expand, paginate=paginate)


    def get_groups(self, limit=1000, expand=None, paginate=True):
        """
        Returns a list of groups, limited in number by {limit}.
        """
        return self.get(f"{self.baseurl}/wiki/rest/api/group", limit=limit, expand=expand, paginate=paginate)


    def get_group_members(self, group_id, limit=200, expand=None, paginate=True):
        """
        Returns a list of groups members of group {group_id}, limited in number by {limit}.
        """
        return self.get(f"{self.baseurl}/wiki/rest/api/group/{group_id}/membersByGroupId", limit=limit, expand=expand, paginate=paginate)


    def convert_to_guest_user(self, user_id, guest_group_id):
        """
        Coverts a user, identified by {user_id}, to a guest user by adding them to the guest group, identified by {guest_group_id}.
        Will handle removing other groups if need be.
        """

        # get user's group memberships
        user_group_memberships = self.get_user_group_memberships(user_id)

        # check if the user already is a guest user
        if len(user_group_memberships) == 1 and user_group_memberships[0]['id'] == guest_group_id:
            return


        # remove user from all current groups
        for group in user_group_memberships:
            self.remove_user_from_group(user_id, group['id'])

        # remove the user from all current groups
        

        #pdb.set_trace()
        # add user to the guest group
        return self.add_user_to_group(user_id, guest_group_id)


    def add_user_to_group(self, user_id, group_id):
        """
        Adds a user, identified by {user_id}, to a group, indentified by {group_id}.
        """
        # define url and payload
        url     = f"{self.baseurl}/wiki/rest/api/group/userByGroupId"
        query   = {
                    'groupId' : group_id
                  }
        payload = json.dumps({
                                'accountId' : user_id,
                             })

#        pdb.set_trace()
        return self.post(url, params=query, data=payload)




    def remove_user_from_group(self, user_id, group_id):
        """
        Removes a user, identified by {user_id}, from a group, indentified by {group_id}.
        """
        # define url and payload
        url     = f"{self.baseurl}/wiki/rest/api/group/userByGroupId"
        query   = {
                    'groupId'   : group_id,
                    'accountId' : user_id,
                  }

        #pdb.set_trace()
        return self.delete(url, params=query)




    def get_user_group_memberships(self, user_id):
        """
        Fetch a list of all groups a user is member of.
        """

        # define url and payload
        url     = f"{self.baseurl}/wiki/rest/api/user/memberof"
        query   = {
                    'accountId' : user_id
                  }

        return self.get(url, params=query)














