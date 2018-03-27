#!/usr/bin/python
#! -*- coding: utf-8 -*-
import logging
import sys
import supr
import os

from irods.session import iRODSSession
from irods.exception import *
import settings

from supr_common import (asciify,
                         sendMail,
                         setup_log,
                         temp_password)

logging.basicConfig()
# logging configuration
logger              = setup_log("IRODS_SET_PWD", "logs/irods_set_pwd_1time.log")

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

try:

	# Connection to a server with the default values
	sess = iRODSSession(host=settings.IRODS_HOST, 
			    port=settings.IRODS_PORT, 
			    user=settings.IRODS_ADMIN_USER, 
			    password=settings.IRODS_ADMIN_PWD, 
			    zone=settings.IRODS_ZONE)

	memberList = ['s_dejvi', 's_ilako']

	for p in res.matches:

		for m in p.members:

			userName = str(m.centre_person_id).strip()
			
			if userName and (userName not in memberList):

				principal = userName+ "@SWESTORE.SE"

				try:
					user = sess.users.get(userName)
					if user:
						memberList.append(userName)
						sess.users.modify(userName, 'password', temp_password())
						logger.info(userName + " -- temp password added to irods")

						if (not user.dn) or (user.dn and principal not in user.dn):
							sess.users.modify(userName, 'addAuth', principal)
							logger.info(userName + " -- principal added to irods")
						else:
							logger.info(userName + " -- principal already added to irods")

						if m.subject and not m.subject == "":
							certi_subj = str((m.subject).encode('utf-8'))

							if user.dn and certi_subj not in user.dn:
								sess.users.modify(userName, 'addAuth', certi_subj)
								logger.info(userName + " certificate added to irods auth")
							else:
								logger.info(userName + " -- certificate already added to irods")

				except UserDoesNotExist:
					print userName + "does not exist in irods"
					logger.info(userName + " user does not exist in irods")

			else:
				logger.info(userName + " -- temp password already added to irods")

except iRODSException as ie:
	logger.error("Error during iRODS Connection: %s", repr(ie))

except Exception as e:
	logger.error("Error during Execution: %s", e)
finally:
	if sess:
		sess.cleanup()
