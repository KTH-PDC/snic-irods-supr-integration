#!/usr/bin/python
#! -*- coding: utf-8 -*-

import ipahttp
import logging
import sys
import supr
import settings
import requests

from requests import ConnectionError
logging.basicConfig()
requests.packages.urllib3.disable_warnings()


from supr_common import (asciify,
                         sendMail,
                         setup_log)

logger              = setup_log("IPA_ADD_USER", settings.IPA_LOG_FILE)



# Function to add new Person to FREEIPA
def addPersontoFreeIPA(m):
	try:
		uidNumber = str(settings.uidNumberStart + m.id)
		user = m.centre_person_id
		opts = {"givenname": m.first_name, 
			"sn": m.last_name, 
			"mail" : m.email, 
			"uidnumber": uidNumber,
			#"description":str(m.id),
			}
		result = ipa.user_add(user, opts)
                print result
		logger.info(user + " added to IPA")

	except Exception as e:
		logger.error("Error in addPersontoFreeIPA Module for %s :: %s", str(uidNumber), e)


# Search in SUPR
try:
	# Prepare a SUPR connection object
	supr_connection = supr.SUPR(user = settings.SUPR_API_USER_NAME, 
				    password = settings.SUPR_API_PASSWORD,
				    base_url = settings.SUPR_BASE_URL)

	# Compose query from the below options
	params = {'full_person_data': '1','resource_centre_id': settings.resource_centre_id}

	res = supr_connection.get("project/search/", params = params)
except supr.SUPRHTTPError as e:
	# Logging Errors from SUPR
	logger.error("HTTP error from SUPR - %s" %e.text)
	sendMail("HTTP error from SUPR - " + e.text, settings.FROM_ADDRS, settings.IRODS_ADMIN_MAIL, "SUPR - SWESTORE Connection Error")
	sys.exit(1)
except ConnectionError as ce:
	logger.error("Connection to SUPR failed - %s" %str(ce))
	sendMail("Connection to SUPR failed - " + str(ce), settings.FROM_ADDRS, settings.DCACHE_ADMIN_MAIL, "SUPR - SWESTORE Connection Error")
	sys.exit(1)

# Connect to FreeIPA
try:
	ipa = ipahttp.ipa(settings.IPA_HOST)
	ipa.login(settings.IPA_ADMIN_USER, settings.IPA_ADMIN_PWD)
except Exception as e:
	logger.error("FreeIPA Connection Error - %s", e)
	sendMail("Error occured in FreeIPA Connection - " + str(e), settings.FROM_ADDRS, settings.IRODS_ADMIN_MAIL, "IPA Connection Error")
	sys.exit(1)

# Loop through the results from the search in SUPR
for p in res.matches:
	for m in p.members:
		user = m.centre_person_id
                print user 
		reply = ipa.user_find(user)
		if reply['result']['result']:
			logger.info(user + " already exists in IPA")
		else:
			addPersontoFreeIPA(m)
