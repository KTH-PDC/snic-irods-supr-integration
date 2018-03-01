#!/usr/bin/python
#! -*- coding: utf-8 -*-
import logging
import sys
import supr
import settings
import requests

from requests import ConnectionError
requests.packages.urllib3.disable_warnings()

from supr_common import (setup_log, sendMail)

logger              = setup_log("SUPR_SUA", "logs/supr_sua_check.log")

# Message to be sent to User
def sendUserMail(m, proj_name):

	msgTxt  = "Dear " + m.first_name + " " + m.last_name + ",\n \n"
	msgTxt += "You are receiving this mail as you are a member of Swestore project -- " + proj_name + " in SUPR. \n \n"
	msgTxt += "We have noticed that you have not signed SNIC User Agreement, SUA. \n"
	msgTxt += "Due to a oversight from our side, access to Swestore projects were granted even when this SUA wasn't signed. \n \n"
	msgTxt += "To be able to use Swestore in the future, it is important that SUA is accepted.\n"
	msgTxt += "Please login to SUPR (https://supr.snic.se/login). Go to Personal Information and sign the SUA using Federated Identity. \n\n"
	msgTxt += "In case of any issues or clarifications, please mail support@swestore.se. \n\n"
	msgTxt += "Regards,\n" + "SWESTORE Support Team"

	sendMail(msgTxt, 'support@swestore.se', m.email, "Notification to Sign SNIC User Agreement (SUA) in SUPR")

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

		for m in p.members: 
			if m.user_agreement_version and m.user_agreement_accepted:
				logger.info(m.centre_person_id + " SUA is signed and accepted")
			else:
				logger.info(m.centre_person_id + " SUA is not signed and accepted")
				print(m.centre_person_id + " SUA is not signed and accepted")
				#sendUserMail(m, p.name)

except supr.SUPRHTTPError as e:
	# Logging Errors from SUPR
	logger.error("HTTP error from SUPR - %s" %e.text)
	sys.exit(1)
except ConnectionError as ce:
	logger.error("Connection to SUPR failed - %s" %str(ce))
	sys.exit(1)

