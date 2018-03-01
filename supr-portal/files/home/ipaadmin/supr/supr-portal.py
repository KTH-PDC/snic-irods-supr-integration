#!/bin/python

#! -*- coding: utf-8 -*-

# Second part of SUPR authentication script.

# System imports.
import os
import sys
import datetime
import random
import subprocess

# Cookie handling, included with python.
import cookielib
import Cookie
import urllib2
import requests
import pickle

# SUPR definitions.
sys.path.append("/home/ipaadmin/supr")
import supr
from supr_auth import get_session_cookie, msghtml, msghead

# Get the arguments.
token = sys.argv[1]
password = sys.argv[2]
verification = sys.argv[3]

# Get the saved cookies.
fn = "/home/ipaadmin/supr/cookies." + token + ".dict"

# Create the request session object and load the cookies.
s = requests.session()
try:
    with open(fn, 'rb') as f:
        sdd = pickle.load(f)
        s.cookies.update(sdd)
except IOError:
    msghtml("Portal Authentication Error",
        "Cannot find autentication information");
    sys.exit (1)

# From the saved cookies we got.
tk = sdd["session"]
id = sdd["id"]
fname = sdd["first_name"]
lname = sdd["last_name"]
cpi = sdd["cpi"]

# Fail out when the token does not match.
if token != tk:
    msghtml("Portal Authentication Error",
        "Cannot find autentication information");
    sys.exit (1)

# Go ahead and change the password.
try:
    cmdout = subprocess.check_output(
        [ "/home/ipaadmin/bin/ipa-passwd", cpi, password ],
        stderr=subprocess.STDOUT)
except subprocess.CalledProcessError as e:
    msghtml("Portal Password Change Error",
        "Error changing password for " + cpi + " error " +
            str(e.returncode))
    sys.exit(1)

# Finish.
sys.exit(0)

