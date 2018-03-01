#!/usr/bin/python
#! -*- coding: utf-8 -*-
import logging
import sys
import supr
import smtplib
import os

from email.mime.text import MIMEText
from irods import *
from settings import *
from subprocess import call, check_output

# logging configuration
logging.basicConfig(filename = DELETE_LOG_FILE, 
		    filemode = LOG_FILE_MODE,
		    format = LOG_FILE_FORMAT,
		    datefmt = LOG_FILE_DATEFORMAT,
		    level = logging.DEBUG)

# Compose query from the below options
params = {'full_person_data': '1','resource_centre_id': resource_centre_id, 'resource_id': irods_resource_id}

# Search in SUPR
try:
	# Prepare a SUPR connection object
	supr_connection = supr.SUPR(user = SUPR_API_USER_NAME, password = SUPR_API_PASSWORD)

	# Get All Projects
	res = supr_connection.get("project/search/", params = params)
except supr.SUPRHTTPError as e:
	# Logging Errors from SUPR
	logging.error("HTTP error from SUPR - %s" %e.text)
	sys.exit(1)

try:
sess = None
coll = None
group = None

try:

	# Connection to a server with the default values
	sess = iRODSSession(host=settings.IRODS_HOST, 
			    port=settings.IRODS_PORT, 
			    user=settings.IRODS_ADMIN_USER, 
			    password=settings.IRODS_ADMIN_PWD, 
			    zone=settings.IRODS_ZONE)

	try:
		c = sess.collections.get(settings.IRODS_DIR)
		self.logger.info("Client Connection to iRODS successful \n")
	except CollectionDoesNotExist:
		self.logger.error(settings.IRODS_DIR + " does not exist ")
		self.ERR_MJR_MAIL += settings.IRODS_DIR + " does not exist " + "\n"
		self.err_mjr_cnt  += 1

	try:
		userGroup  = sess.user_groups.get("users")
	except UserGroupDoesNotExist:
		self.logger.error(" users group does not exist ")
		self.ERR_MJR_MAIL += " users group does not exist " + "\n"
		self.err_mjr_cnt  += 1

	for p in res.matches:

		proj_name = ((p.directory_name).encode('utf-8')).lower()
		group = sess.user_groups.get(proj_name)

		for m in p.members:
			if m.centre_person_id:
				userName = str(m.centre_person_id).strip()

			user = sess.users.get(userName)
			if group:
				if user and group.hasmember(userName):
					group.removemember(userName)
					logging.info(userName + " user deleted from " + proj_name + " group")
				else:
					logging.info(userName + " user already deleted from " + proj_name + " group")

			if userGroup:
				if user and userGroup.hasmember(userName):
					userGroup.removemember(userName)
					logging.info(userName + " user deleted from user group")
				else:
					logging.info(userName + " user already deleted from users group")

			if user:
				sess.users.remove(userName)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        
				logging.info(userName + " user deleted.")
			else:
				logging.info(userName + " user already deleted")

		if group:
			sess.user_groups.remove(proj_name)
			sess.collections.remove(proj_name)
			logging.info(proj_name + " group deleted")
		else:
			logging.info(proj_name + " group already deleted")

except Exception as e:
	logging.error("Error during Execution: %s", e)
finally:
	if sess:
		sess.cleanup()

