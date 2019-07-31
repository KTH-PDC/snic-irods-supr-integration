#!/usr/bin/python
#! -*- coding: utf-8 -*-
import ldap
import ldap.modlist as modlist
import logging
import sys
import supr
import smtplib
import os

from email.mime.text import MIMEText

import settings

from supr_common import (asciify,
                         sendMail,
                         setup_log,
                         temp_password)

logging.basicConfig()
# logging configuration
logger              = setup_log("Yubikey_Mail", "logs/yubikey_mail_1time.log")

# Compose query from the below options
params = {'full_person_data': '1','resource_centre_id': settings.resource_centre_id, 'resource_id': settings.irods_resource_id}

# Search in SUPR
try:
	# Prepare a SUPR connection object
		# Prepare a SUPR connection object
	supr_connection = supr.SUPR(user = settings.SUPR_API_USER_NAME, 
				    password = settings.SUPR_API_PASSWORD,
				    base_url = settings.SUPR_BASE_URL)

	# Get All Projects
	res = supr_connection.get("project/search/", params = params)
except supr.SUPRHTTPError as e:
	# Logging Errors from SUPR
	logger.error("HTTP error from SUPR - %s" %e.text)
	sys.exit(1)


sess = None

# Message to be sent to User
def sendUserMail(m, proj_name):

	msgTxt  = "Dear " + m.first_name + " " + m.last_name + ",\n \n"
	msgTxt += "You are receiving this mail as you are a member of Swestore/iRODS project -- " + proj_name + " in SUPR. \n\n"

	msgTxt += "We would like to inform that going forward SNIC/iRODS will be using password authentication and yubikey would be retired. \n"
	msgTxt += "Please click on the following link to set password -- http://auth1.swestore.se/ipa/supr/supr-auth1.cgi \n"
	msgTxt += "You will be redirected to SUPR authentication page for confirmation. \n"
	msgTxt += "Once authenticated, you can set a password for iRODS. \n \n"
	msgTxt += "We also request you to mail us back the yubikey to the following address -- \n \n"
	msgTxt += "Krishnaveni Chitrapu \n"
	msgTxt += "Swestore/iRODS Support Team \n"
	msgTxt += "National Supercomputer Centre \n"
	msgTxt += "Linköping University \n"
	msgTxt += "581 83 Linköping, Sweden \n \n"

	msgTxt += "For more information on connecting and using snic-irods,\n"
	msgTxt += "please refer to http://snicdocs.nsc.liu.se/wiki/Swestore-irods \n \n"
	msgTxt += "Regards,\n" + "Swestore/iRODS Support Team"

	msgTxt = msgTxt.decode('utf-8')

	sendMail(msgTxt, settings.IRODS_FROM_ADDRS, m.email, "IRODS - Yubikey authentication replaced with password authentication")

try:

	memberList = []
	for p in res.matches:
		proj_name = ((p.directory_name).encode('utf-8')).lower()
		for m in p.members:

			if m.id not in memberList:

				memberList.append(m.id)
				sendUserMail(m,proj_name)
				logger.info("mail sent to -- " + str(m.id))

			else:
				logger.info("mail already sent to -- " + str(m.id))

except Exception as e:
	logger.error("Error during Execution: %s", e)
finally:
	if sess:
		sess.cleanup()
