#!/usr/bin/python
#! -*- coding: utf-8 -*-
import ldap
import ldap.modlist as modlist
import sys

import settings


# LDAP search scope and other variables
searchScope = ldap.SCOPE_SUBTREE
retrievedAttrs = ["description"]

# Delete Persons from LDAP and iRODS that are not in SUPR
def deletePersons():
	try:
		# Get All Persons from LDAP
		filter = "uidNumber=*"
		ldap_result_id = l.search(settings.peopleDN, searchScope, filter, retrievedAttrs)
		result_type, ldap_persons = l.result(ldap_result_id)

		# Loop through LDAP results
		for person in ldap_persons:
			l.delete_s(person[0])

	except ldap.LDAPError as le:
		print("LDAP Error in deletePersonsFromLDAP Module - %s", le)

# Delete Projects from LDAP and iRODS that are not in SUPR
def deleteProjects():
	try:
		# Get All Projects from LDAP
		filter = "gidNumber=*"
		ldap_result_id = l.search(settings.groupsDN, searchScope, filter, retrievedAttrs)
		result_type, ldap_groups = l.result(ldap_result_id)
		
		for group in ldap_groups:
			l.delete_s(group[0])

	except ldap.LDAPError as le:
		print("LDAP Error in deleteProjectsFromLDAP Module - %s", le)


# Connect to LDAP using python-LDAP
ldap.set_option(ldap.OPT_X_TLS_CACERTFILE,settings.TLS_CACERTFILE)
ldap.set_option(ldap.OPT_X_TLS_CERTFILE,settings.TLS_CERTFILE)
ldap.set_option(ldap.OPT_X_TLS_KEYFILE,settings.TLS_KEYFILE)
ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT,ldap.OPT_X_TLS_DEMAND)

l = ldap.initialize(settings.LDAP_HOST)

try:
	l.simple_bind(settings.LDAP_ADMIN, settings.LDAP_PASSWORD)

	# delete Persons From LDAP
	deletePersons()

	# delete Projects From LDAP
	deleteProjects()

except ldap.LDAPError as le:
	print("LDAP Connection Error - %s", le)
finally:
	if l:
		l.unbind()
