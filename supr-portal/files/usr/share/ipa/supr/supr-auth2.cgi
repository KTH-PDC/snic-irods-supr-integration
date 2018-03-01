#!/bin/sh

# SUPR Authentication part 2.

# We are running as a CGI script so we got the argument in
# the environment variable. This is the cookie string coming from SUPR.
# Cut off the first part, leave just the hex string.
QUERY_STRING="`echo $QUERY_STRING | sed 's/^.*=//'`"
export QUERY_STRING

# Run the authenticator pass 2 in ipaadmin context.
sudo -u ipaadmin /home/ipaadmin/supr/supr-auth2.py "${QUERY_STRING}"

# Finish.
exit 0

