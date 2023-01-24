# confluence-server-to-cloud-utils

Collection of various scripts used to migrate a Confluence Server to Confluence Cloud.

## Prefixing of spaces
Script used: `prefix_spaces_on_confluence-server.py`

We wanted to prefix all space names from the Server instance with a recognizable work to have a way to separate them from the spaces already existing in the Cloud instance. This script is run against the Confluence Server API to prefix all spaces before migrating them to Confluence Cloud.

## Changing eligable users to single space guest users
Script used: `change_users_to_single_space_guests.py`

The Cloud version recently started with a new type of user that is free to have, the [single space guest](https://support.atlassian.com/confluence-cloud/docs/invite-guests-for-external-collaboration/). The only requirement is that the user is only member of a single space. This script is run against the Confluence Cloud API after the migration has been completed.
