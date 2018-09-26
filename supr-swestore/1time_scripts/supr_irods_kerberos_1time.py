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
                         setup_log)

logging.basicConfig()
# logging configuration
logger      = setup_log("IRODS_PDC_KERBEROS", "logs/irods_set_pdc_kerberos_1time.log")

# Compose query from the below options
params = {'full_person_data': '1','all_centre_person_ids':'1', 'resource_centre_id': settings.resource_centre_id, 'resource_id': settings.irods_resource_id}

# Search in SUPR
try:
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

    memberList = []

    for p in res.matches:

        for m in p.members:

            userName = None
            if m.centre_person_id:
                userName = str(m.centre_person_id).strip()

            if userName and (userName not in memberList):

                try:
                    user = sess.users.get(userName)
                    if user:
                        memberList.append(userName)

                        if m.centre_person_ids:
                            pdc_kerberos_principal = None

                            for cpid in m.centre_person_ids:
                                if cpid.centre.id == settings.PDC_centre_id:

                                    pdc_kerberos_principal = cpid.centre_person_id + "@" + settings.PDC_kerberos
                                    #print pdc_kerberos_principal

                                    if (not user.dn) or (user.dn and pdc_kerberos_principal not in user.dn):
                                        #print user.dn
                                        sess.users.modify(userName, 'addAuth', pdc_kerberos_principal)
                                        logger.info(pdc_kerberos_principal + " -- PDC Kerberos principal added to irods user -- " + userName)
                                    else:
                                        logger.info(pdc_kerberos_principal + " -- PDC Kerberos principal already added to irods user -- " + userName)

                except UserDoesNotExist:
                    logger.info(userName + " user does not exist in irods")

            else:
                logger.info(userName + " -- user already checked")

except iRODSException as ie:
    logger.error("Error during iRODS Connection: %s", repr(ie))

except Exception as e:
    logger.error("Error during Execution: %s", e)
finally:
    if sess:
        sess.cleanup()

