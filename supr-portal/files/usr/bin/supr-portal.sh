#!/bin/sh

# SUPR portal request script.

# Run test script as ipaadmin, get credentials there.
sudo -u ipaadmin /home/ipaadmin/supr/supr-portal.py "$1" "$2" "$3"
exit $?

