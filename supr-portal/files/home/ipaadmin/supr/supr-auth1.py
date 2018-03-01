#!/bin/python

#! -*- coding: utf-8 -*-

# First part of SUPR authentication.

# System definitions.
import os
import sys

# SUPR definitions.
sys.path.append("/home/ipaadmin/supr")
import supr
from supr_auth import msghtml, msghead

# SUPR authenticator URL base (test).
base_url = "https://disposer.c3se.chalmers.se/supr-test/api"

# Redirect URL, redirect to second part.
return_url = "https://auth1.swestore.se/ipa/supr/supr-auth2.cgi"

# Message to show, passed on to SUPR API.
message = "Login to use IPA services"

# SUPR API credentials file.
credfile = "/home/ipaadmin/supr/credentials.txt"

# Get SUPR API username and password from a file.
try:

    # Open file and read blank separated username and password.
    f = open(credfile)
    username, password = f.read().strip().split(None,1)
    f.close()
except Exception:

    # Exit when error reading file.
    msghtml("SUPR Authentication Error", "Cannot find credentials file " +
        credfile)
    sys.exit(1)

# Initiate SUPR authentication API call.
s = supr.SUPR(username, password, base_url)
try:

    # RPC the authenticator.
    response = s.post("/centreauthentication/initiate/",
        data = dict(return_url = return_url, message = message))

    # Token and redirect URL returned.
    token = response['token']
    url = response['authentication_url']
except supr.SUPRException:

    # Call failure, quit.
    msghtml("SUPR Authentication Error",
        "Cannot initiate autentication process")
    sys.exit(1)

# Issue redirect and pass the token, we are running as cgi.
msghead('<meta http-equiv="refresh" content="0; url='+ url + '">')

# Finish.
sys.exit(0)

