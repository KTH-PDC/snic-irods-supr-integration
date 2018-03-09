#!/usr/bin/python
#! -*- coding: utf-8 -*-

import datetime
import logging
from requests import ConnectionError
import sys
import supr

import settings
import supr_ldap

from supr_common import (setup_log,
			 sendMail)

# logging configuration
log_main = setup_log('SUPR_SWESTORE', settings.LOG_FILE)

# getting modified_since time from file
try:
	with open("modified_time.txt", "r") as f:
		t = f.readline()

		if t:
			t = t.strip("\n")

		log_main.info("Modified Since : %s" %t)

except IOError as ie:
	log_main.error("Error occured in reading modified_time.txt file :: " + ie)
	sendMail(ie.text, settings.FROM_ADDRS, settings.DCACHE_ADMIN_MAIL, "SUPR SWESTORE MAIN")

# Search in SUPR
try:
	# Prepare a SUPR connection object
	supr_connection = supr.SUPR(user = settings.SUPR_API_USER_NAME, 
				    password = settings.SUPR_API_PASSWORD,
				    base_url = settings.SUPR_BASE_URL)

	# Compose query from the below options
	params = {'full_person_data': '1','resource_centre_id': settings.resource_centre_id, 'modified_since': t}

	res = supr_connection.get("project/search/", params = params)
except supr.SUPRHTTPError as e:
    # Logging Errors from SUPR
    log_main.error("HTTP error from SUPR - %s" %e.text)
    sendMail("HTTP error from SUPR - " + e.text, settings.FROM_ADDRS, settings.DCACHE_ADMIN_MAIL, "SUPR - SWESTORE Connection Error")
    sys.exit(1)
except ConnectionError as ce:
	log_main.error("Connection to SUPR failed - %s" %str(ce))
	sendMail("Connection to SUPR failed - " + str(ce), settings.FROM_ADDRS, settings.DCACHE_ADMIN_MAIL, "SUPR - SWESTORE Connection Error")
	sys.exit(1)

all_projects     = []
persons_modified = []


# Loop through the results from the search in SUPR
for p in res.matches:

	all_projects.append(p)


# Search in SUPR
try:
	# Compose query from the below options
	params = {'modified_since': t}

	res = supr_connection.get("person/search/", params = params)
except supr.SUPRHTTPError as e:
    # Logging Errors from SUPR
    log_main.error("HTTP error from SUPR - %s" %e.text)
    sendMail("HTTP error from SUPR - " + e.text, settings.FROM_ADDRS, settings.DCACHE_ADMIN_MAIL, "SUPR - SWESTORE Connection Error")
    sys.exit(1)
except ConnectionError as ce:
	log_main.error("Connection to SUPR failed - %s" %ce.text)
	sendMail("Connection to SUPR failed - " + ce.text, settings.FROM_ADDRS, settings.DCACHE_ADMIN_MAIL, "SUPR - SWESTORE Connection Error")
	sys.exit(1)

# Getting the updated Person profiles using modified_since
for m in res.matches:
	persons_modified.append(m)

# call to function to add projects to LDAP
if all_projects or persons_modified:

	if all_projects:
		all_projects.sort(key = lambda p: p.id)
	if persons_modified:
		persons_modified.sort(key = lambda m: m.id)

	supr_ldap.SUPR_LDAP(all_projects, persons_modified, supr_connection)

# updating modified_since time to file
try:
	#t = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	t = res.began
	with open("modified_time.txt", "w") as f:
		f.write(t)
		log_main.info("Updated Modified Since to: %s \n" %t)

except IOError as ie:
	log_main.error("Error occured in updating modified_time.txt file :: " + ie + "\n")
	sys.exit(1)
