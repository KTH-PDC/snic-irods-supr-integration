#!/usr/bin/python
#! -*- coding: utf-8 -*-

import datetime

# Settings File for supr_swestore

# SUPR API USER NAME
SUPR_API_USER_NAME  = "api-c-9"
# SUPR API PASSWORD
SUPR_API_PASSWORD   = #Get password from SUPR
# SUPR API URL
SUPR_BASE_URL       = "https://supr.snic.se/api/"

# LDAP HOST
HOST_NAME           = "ldap1.swestore.se"
LDAP_PORT           = "636"
LDAP_HOST           = "ldaps://" + HOST_NAME + ":" + LDAP_PORT
#LDAP_HOST          = "ldapi:///"
# LDAP BIND DN
baseDN              = "dc=swestore-ldap"
LDAP_ADMIN          = "cn=admin," + baseDN
# LDAP BIND PASSWORD
LDAP_PASSWORD       = # LDAP Password

# TLS Certificate Paths
#TLS_CACERTDIR       = "/etc/openldap/certs/"
TLS_CACERTFILE      = "/etc/grid-security/certificates/TERENA-eScience-SSL-CA-3.pem"
TLS_CERTFILE        = "/etc/grid-security/supr-cert.pem"
TLS_KEYFILE         = "/etc/grid-security/supr-key.pem"

# LDAP DN
groupsDN            = "ou=Groups," + baseDN 
peopleDN            = "ou=People," + baseDN
uidNumberStart      = 30000
gidNumberStart      = 6000

# Centre Resource ID in SUPR for Swestore
resource_centre_id  = 9

# iRODS Resource ID in SUPR
irods_resource_id   = 32

# dcache Resource ID in SUPR for Swestore
dcache_resource_id  = 31

# IRODS Settings for connection

IRODS_DIR           = "/snic.se/projects"
IRODS_HOME_DIR      = "/snic.se/home"
IRODS_HOST          = "snic2-irods.nsc.liu.se"
IRODS_PORT          = 2432
IRODS_ADMIN_USER    = "supr"
IRODS_ADMIN_PWD     = # irods admin password
IRODS_ZONE          = "snic.se"

# FreeIPA User
IPA_HOST	    =  "auth1.swestore.se"
IPA_ADMIN_USER	    =  "supr"
IPA_ADMIN_PWD	    =  # IPA Admin password
 
# Get a date object
today               = datetime.date.today().strftime("%Y-%m-%d")

BASEDIR             = "/supr/"
IRODS_LOG_FILE      = BASEDIR + "logs/irods_" + str(today) + ".log"
DELETE_LOG_FILE     = BASEDIR + "logs/delete_" + str(today) + ".log"
LOG_FILE            = BASEDIR + "logs/ldap_" + str(today) + ".log"
IPA_LOG_FILE        = BASEDIR + "logs/ipa_" + str(today) + ".log"
LOG_FILE_MODE       = 'a'
LOG_FILE_FORMAT     = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE_DATEFORMAT = '%H:%M:%S'

# DCache Admin Mail Ids to send mail
DCACHE_ADMIN_MAIL   = 'dcache-admin@swestore.se'
# iRODS Admin Mail Ids to send mail
IRODS_ADMIN_MAIL    = 'irods-admin@swestore.se'

# Send Mail Attributes
SMTP_HOST           = 'localhost'
SMTP_PORT           = 25

FROM_ADDRS          = 'supr@' + HOST_NAME
IRODS_FROM_ADDRS    = 'irods-admin@swestore.se'

LDAP_SUBJECT        = "SUPR - SWESTORE LDAP Integration Daily Mail"
IRODS_SUBJECT       = "SUPR - SWESTORE IRODS Integration Daily Mail"
LDAP_DEL_SUBJECT    = "SUPR - SWESTORE LDAP Deletion Mail"
IRODS_DEL_SUBJECT   = "SUPR - SWESTORE IRODS Deletion Mail"
IRODS_USR_SUBJECT   = "SNIC - iRODS Username and Project Path"
