#!/usr/bin/python
#! -*- coding: utf-8 -*-
import ldap
import ldap.modlist as modlist

from settings import *

# Connect to LDAP using python-LDAP
try:
	#ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
	#l = ldap.initialize(LDAP_HOST)
	l = ldap.open(LDAP_HOST)
	l.simple_bind_s(LDAP_ADMIN, LDAP_PASSWORD)

	attrs = {}
	attrs['objectclass'] = ['top','organization','dcObject']
	attrs['o'] = 'Swestore'

	ldif = modlist.addModlist(attrs)
	l.add_s(baseDN,ldif)

        attrs = {}
	attrs['objectclass'] = ['top','organizationalUnit']
	attrs['ou'] = 'Groups'
	
	ldif = modlist.addModlist(attrs)
	l.add_s(groupsDN,ldif)
	
	attrs = {}
	attrs['objectclass'] = ['top','organizationalUnit']
	attrs['ou'] = 'People'
	
	ldif = modlist.addModlist(attrs)
	l.add_s(peopleDN,ldif)
		
	l.unbind_s()
		
except ldap.LDAPError, e:
	print e	
