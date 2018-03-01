#!/bin/python

#! -*- coding: utf-8 -*-

# SUPR portal request script. Called from the IPA server
# rpcserver.py script, from whithin the custom class.

# Enable system functions.
import os
import os.path
import sys
import subprocess

# Show message in html.
def msghtml(title, message):
    print "Content-type: text/html"
    print ""
    print "<html>"
    print "<head>"
    print "<title>" + title + "</title>"
    print "</head>"
    print "<body>"
    print message
    print "</body>"
    print "</html>"

# Title for messages.
t = 'Supr portal user exit script'

# IPA admin SUPR portal script to run.
supr_portal_script = '/home/ipaadmin/supr/supr-portal.py'

# Arguments to the script. Session cookie, password, verification.
narg = len(sys.argv)
if narg != 4:
    msghtml (t, 'Wrong number of arguments to supr portal script')
    sys.exit(1)
se = sys.argv[1]
pw = sys.argv[2]
ve = sys.argv[3]

# Switch to ipaadmin and get admin credentials there.
result = 'unknown failure'
try:

    # Call the script passing arguments.
    # No shell (which is the default), capture stderr also.
    cmdout = subprocess.check_output(
        [
            '/usr/bin/sudo',
            '-u',
            'ipaadmin',
            supr_portal_script,
            se, pw, ve ],
        stdin=None, stderr=subprocess.STDOUT, shell=False)

    # Return if success.
    result = 'ok'
    message = cmdout
except subprocess.CalledProcessError as e:

    # Exception with non-zero return code.
    result = 'failure ' + str(e.returncode)
    message = e.output

# There was an error so report it.
if result != 'ok':

    # Message from the call out script should be the error report
    # and it is already html-ized.
    print message
    sys.exit(1)

# Finish with success.
sys.exit(0)

