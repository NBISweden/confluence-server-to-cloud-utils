import requests
from requests.auth import HTTPBasicAuth
import json
import pdb
import logging
import re




def name_processor(name):
    """
    Helper function to normalize names to lowercase, no spaces or special characters
    """
    return re.sub("[^a-z0-9]", '', name.lower())




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






    def get(self, url, params=None, data=None, paginate=True):
        """
        Wrapper function to make API calls that will keep sending subsequent requests if the answer is paginated.
        """


#        pdb.set_trace()
        logging.debug(f"Fetching URL: {url}")

        # fetch results
        response = requests.request("GET", url, headers=self.headers, params=params, data=data, auth=self.auth,).json()

        # keep asking for more until there is no more or the limit is reached
        #pdb.set_trace()
        if response['size'] <= params.get('limit', 10000) and paginate:

            logging.debug(f"Possible API pagination detected, continuing sending more requests.")

            # save inital response
            results = response['results']

            # loop until all hits are collected
            i = 0
            while response['results'] and len(results) < params.get('limit', 10000):


                logging.debug(f"Fetching URL: {url} starting from {len(results) + 1}")

                # set new start point for query
                params['start'] = len(results) + 1

                # ask for a new batch of results
                response = requests.request("GET",
                                            url,
                                            headers=self.headers,
                                            params=params,
                                            data=data,
                                            auth=self.auth,
                                            ).json()

                # save the new batch together with the previous ones
                results += response['results']

                # increase counter
                i+=1
            
            logging.debug(f"API pagination finished, {i} pages fetched.")

        else:
            # got them all in the first request
            results = response['results']

        # return at most the limit the user asked for, if any
        return results[:params.get('limit', 10000)]





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
        payload = f'{{"name": "{name}"}}'

        logging.debug(f"Putting URL: {url}\tPayload: {payload}")
        #pdb.set_trace()
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






    def get_groups(self):
        """
        Returns a list of all groups.
        """

        # get all groups
        url = f"{self.baseurl}/rest/api/group"
        params = {
                    'limit':1000,
                 }
        return self.get(url, params=params)





    def get_group_members(self, group_name):
        """
        Returns a list of all users who are members of a group.
        """

        # get all group members
        url = f"{self.baseurl}/rest/api/group/{group_name}/member"
        params = {
                    'limit':1000,
                 }
        return self.get(url, params=params)





    def get_users(self):
        """
        Returns a list of most users. Will miss disabled accounts that are not members of any groups.
        """


        ### group based method, won't return users not in any groups, and will have duplicates of users in multiple groups

        # get all groups
        groups = self.get_groups()

        # get members of each group
        group_users = []
        for group in groups:
            group_users += self.get_group_members(group['name'])

        ### CQL method, won't return disabled accounts
        search_users = [ user['user'] for user in self.search(cql_query='type=user')]

        # merge lists and remove duplicates based on username
        merged_users = { user['username']:user for user in group_users}
        merged_users.update({ user['username']:user for user in search_users})

        # return as a list of users
        return [ user for user in merged_users.values() ]




    def search(self, cql_query):
        """
        Returns the result of a CQL query (https://developer.atlassian.com/server/confluence/advanced-searching-using-cql/).
        """

        url = f"{self.baseurl}/rest/api/search"
        params = {
                    'cql':cql_query,
                    'limit':1000,
                 }
        return self.get(url, params=params)





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





    def get(self, url, params=None, expand=None, limit=10000, paginate=True):
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
        if len(response['results']) < limit and paginate:

            logging.debug(f"Possible API pagination detected, continuing sending more requests.")

            # save inital response
            results = response['results']

            # loop until all hits are collected
            i = 1
            while response['results'] and len(results) < limit:


                logging.debug(f"Fetching URL: {request_url}&start={ len(results) + 1 }")
                # ask for a new batch of results
                response = requests.request("GET",
                                            f"{request_url}&start={ len(results) + 1 }", 
                                            headers=self.headers,
                                            auth=self.auth,
                                            ).json()

                # save the new batch together with the previous ones
                results += response['results']

                # increase counteults = response['results']
                i+=1
            
            logging.debug(f"API pagination finished, {i} pages fetched.")

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


    def convert_to_guest_user(self, user_id, guest_group_id, remove_other_groups=False):
        """
        Coverts a user, identified by {user_id}, to a guest user by adding them to the guest group, identified by {guest_group_id}.
        Will handle removing other groups if need be.
        """

        # get user's group memberships
        user_group_memberships = self.get_user_group_memberships(user_id)

        # check if the user already is a guest user
        if guest_group_id in [ group['id'] for group in user_group_memberships ]:
            logging.debug(f'Skipping converting users {user_id} to guest since they already are a guest.')

            # skip in that case
            return

        # check if all other groups should be removed
        if remove_user_from_group:
            # remove user from all current groups
            for group in user_group_memberships:
                self.remove_user_from_group(user_id, group['id'])


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





    def add_label_to_space(self, space_key, label, prefix='team'):
        """
        Adds the label {label} to a space, indentified by {space_key}, using the prefix {prefix}.
        """
        # define url and payload
        url     = f"{self.baseurl}/wiki/rest/api/space/{space_key}/label"
        payload = json.dumps([{
                                'prefix' : prefix,
                                'name'   : label,
                             }])
        query = {}

#        pdb.set_trace()
        return self.post(url, params=query, data=payload)





    def remove_label_from_space(self, space_key, label, prefix='team'):
        """
        Removes the label {label} from a space, indentified by {space_key}.
        """
        # define url and payload
        url     = f"{self.baseurl}/wiki/rest/api/space/{space_key}/label"
        query = {
                    'prefix' : prefix,
                    'name'   : label,
                }

#        pdb.set_trace()
        return self.delete(url, params=query)









    def find_possible_guest_users(self, n_spaces=1, ignore_personal_spaces=False, ignore_unlicenced=True, ignore_deleted=True):
        """
        Find all users that are members of maximum {n_spaces} spaces.
        If {ignore_personal_spaces} is True it will not count the personal space (a space with same name as username) to wards this number.
        Will only check if a user is mentioned in a space's permissions, not what permissions they actually have.

        A huge function since there is no way to ask Confluence about what permissions a user has. You have to reconstruct the permissions
        by asking all spaces which users and groups have permission to it, and which group members each group has.
        """

        from fuzzywuzzy import fuzz

        # get a list of all spaces
        spaces = self.get_spaces(expand="permissions")
        
        # init
        user_permissions = {}
        group_permissions = {}
        
        ## Get all user-space and group-space  memberships
        # go through all spaces
        logging.info("Parsing permissions.")
        for space in spaces:
            
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
        
                # if it is a group permission
                elif permission['subjects'].get('group'):
        
                    # for all groups with permission
                    for group in permission['subjects']['group']['results']:
        
                        # save the group and space info
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
        users = self.get_users() 

        # add all users to user_permissions dict to make sure all users are present, even those who don't have any stated permissions in spaces
        for user in users:

            # find missing users
            if user['user']['accountId'] not in user_permissions:

                # initiate entry
                logging.debug(f"Missing user: {user}")
                user_permissions[user['user']['accountId']] = {'spaces':{}, 'user':user['user']}


        # get all groups
        logging.info(f"Fetching groups.")
        groups = self.get_groups()

        # for each groups, get members
        for group in groups:

            # fetch group members
            logging.info(f"Fetching group memebers from {group['name']}")
            members = self.get_group_members(group_id=group['id'])

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



        # make a lookup table for space keys to space names for easy access
        key_to_name = { space['key']:space['name'] for space in spaces}

        # init
        logging.debug(f"Findinig users with {n_spaces} or less spaces.")
        total_users = 0
        found_users = 0

        # find users with access to only n_spaces spaces
        possible_guests = {}
        for user_id,user_perm in user_permissions.items():

            # filter out unlicensed users
            if ignore_unlicenced and 'Unlicensed' in user_perm['user']['displayName']:
                continue

            # filter out deleted users
            if ignore_deleted and 'Deleted' in user_perm['user']['displayName']:
                continue


            # count user towards total
            total_users += 1

            # get the name of the space a user has access to
            user_space_names = None
            if len(user_permissions[user_id]['spaces']) > 0:
                user_spaces = user_permissions[user_id]['spaces'].copy()



            # filter out perosnal spaces if asked to
            if ignore_personal_spaces:

                # go through the names of all spaces the user is a member of
                for user_space_key, user_space in user_permissions[user_id]['spaces'].items():

                    # if the space name is too similar, delete it
                    if fuzz.ratio(name_processor(user_perm['user']['displayName']), name_processor(user_space['name'])) >= 75:
                        del user_spaces[user_space_key]



            # check if the user is a member in few enough spaces to be eligible to be selected
            if len(user_spaces) <= n_spaces:

                # count number of found users
                found_users += 1

                # print user entry
                logging.debug(f"{user_perm['user'].get('displayName', None)}\t{user_perm['user'].get('email', None)}\t{','.join(user_spaces.keys())}")

                # save the user in the keep list
                possible_guests[user_id] = {'user':user_perm['user'], 'spaces':user_perm['spaces']}


        logging.debug(f"Found {found_users} users out of {total_users} total users that are members of {n_spaces} or less spaces.")
        return possible_guests









