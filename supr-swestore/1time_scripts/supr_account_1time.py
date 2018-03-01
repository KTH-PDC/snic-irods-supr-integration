#!/usr/bin/python
#! -*- coding: utf-8 -*-
import logging
import sys
import supr
import settings
import requests

from requests import ConnectionError
requests.packages.urllib3.disable_warnings()

from supr_common import setup_log

logger              = setup_log("SUPR_ACCOUNT", "supr_account_creation")


# Search in SUPR
try:
	# Prepare a SUPR connection object
	supr_connection = supr.SUPR(user = settings.SUPR_API_USER_NAME, 
				    password = settings.SUPR_API_PASSWORD,
				    base_url = settings.SUPR_BASE_URL)

	# Compose query from the below options
	params = {'full_person_data': '1','resource_centre_id': settings.resource_centre_id}

	res = supr_connection.get("project/search/", params = params)

	for p in res.matches:

		resourceIDList = []
		resourceList   = []

		for rp in p.resourceprojects:
			resourceIDList.append(str(rp.resource.id))
			resourceList.append(rp.resource)

		for m in p.members: 
			for resource in resourceList:
				d = {'username' : m.centre_person_id, 
				     'person_id' : m.id,
				     'resource_id' : resource.id,
				     'status' : 'enabled'}
				try:
					account = supr_connection.post("account/create/", data = d)
					logger.info("Account for Person with SUPR ID :: %s for resource -- %s created", m.id, resource.name)
				except supr.SUPRHTTPError as e:
					print e
					# We want to show the text received if we get an HTTP Error
					logger.error("HTTP error in creating account to SUPR - %s :: %s", e.status_code, e)
					#ERR_MJR_MAIL += "Error occured in creating account to SUPR - " + e.text + "\n"
					#ERR_MJR_MAIL += "SUPR ID :: " +  str(m.id) + "\t username(uid) :: " + str(attrsPerson['uid']) + "\t Module :: addPerson \n"
					#err_mjr_cnt  += 1
				except ConnectionError as ce:
					#ERR_MJR_MAIL += "Error occured in creating account to SUPR due to ConnectionError- " + str(ce) + "\n"
					logger.error("Connection to SUPR failed - %s" %str(ce))


except supr.SUPRHTTPError as e:
	# Logging Errors from SUPR
	logger.error("HTTP error from SUPR - %s" %e.text)
	sys.exit(1)
except ConnectionError as ce:
	logger.error("Connection to SUPR failed - %s" %str(ce))
	sys.exit(1)

