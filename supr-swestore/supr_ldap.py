#!/usr/bin/python
#! -*- coding: utf-8 -*-

import ipahttp
import ldap
import ldap.modlist as modlist
import logging
import sys
import supr
import settings
import os, random, string
import requests
import supr_irods_pirc

from requests import ConnectionError
requests.packages.urllib3.disable_warnings()

from supr_common import (asciify,
                         sendMail,
                         setup_log)

class SUPR_LDAP:

	def __init__(self, all_projects, persons_modified, supr_connection):

		if all_projects or persons_modified:
			# Get Logging File Handler
			self.logger          = setup_log(self.__class__.__name__, settings.LOG_FILE)
			self.l               = None
			self.ipa	     = None
			self.irods_projects  = []

			# Get supr_connection
			self.supr_connection = supr_connection

			# LDAP search scope and other variables
			self.searchScope    = ldap.SCOPE_SUBTREE
			self.retrievedAttrs = None

			# Variables needed for calculating number of projects and persons created 
			# that are used to sendMail to Admins
			self.add_proj_cnt   = 0
			self.mod_proj_cnt   = 0
			self.err_proj_cnt   = 0

			self.add_pers_cnt   = 0
			self.mod_pers_cnt   = 0
			self.err_pers_cnt   = 0

			self.err_mjr_cnt    = 0
			self.msgtext        = ""

			# Variables needed for Message Text of projects and persons created 
			# that are used to sendMail to Admins
			self.ADD_PERS_MAIL  = "The Following Persons have been Added on " + settings.today + "\n" 
			self.ADD_PERS_MAIL += "---------------------------------------------------- \n"

			self.MOD_PERS_MAIL  = "The Following Persons have been Modified on " + settings.today + "\n" 
			self.MOD_PERS_MAIL += "---------------------------------------------------- \n"

			self.ADD_PROJ_MAIL  = "The Following Projects have been Added on " + settings.today + "\n" 
			self.ADD_PROJ_MAIL += "----------------------------------------------------- \n"

			self.MOD_PROJ_MAIL  = "The Following Projects have been Modified on " + settings.today 
			self.MOD_PROJ_MAIL += "\n" + "----------------------------------------------------- \n"

			self.ERR_PROJ_MAIL  = "Error in creating the following Projects on " + settings.today + "\n" 
			self.ERR_PROJ_MAIL += "------------------------------------------------------- \n"

			self.ERR_PERS_MAIL  = "Error in creating the following Persons on " + settings.today + "\n" 
			self.ERR_PERS_MAIL += "------------------------------------------------------ \n"

			self.ERR_MJR_MAIL   = "Major Error Occured on " + settings.today + "\n" 
			self.ERR_MJR_MAIL  += "---------------------------------- \n"

			# Connect to LDAP using python-LDAP
			try:
				ldap.set_option(ldap.OPT_X_TLS_CACERTFILE,settings.TLS_CACERTFILE)
				#ldap.set_option(ldap.OPT_X_TLS_CERTFILE,settings.TLS_CERTFILE)
				#ldap.set_option(ldap.OPT_X_TLS_KEYFILE,settings.TLS_KEYFILE)
				ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT,ldap.OPT_X_TLS_NEVER)

				self.l = ldap.initialize(settings.LDAP_HOST)
				#self.l = ldap.open(settings.LDAP_HOST)
				self.l.simple_bind(settings.LDAP_ADMIN, settings.LDAP_PASSWORD)
			except ldap.LDAPError as le:
				self.logger.error("LDAP Connection Error - %s", le)
				if self.l:
					self.l.unbind()

				self.ERR_MJR_MAIL += "Error occured in LDAP Connection - " + str(le) + "\n"
				self.err_mjr_cnt  += 1
				sendMail(self.ERR_MJR_MAIL, settings.FROM_ADDRS, settings.DCACHE_ADMIN_MAIL, settings.LDAP_SUBJECT)
				sys.exit(1)

			# Connect to FreeIPA
			try:
				self.ipa = ipahttp.ipa(settings.IPA_HOST)
				self.ipa.log = setup_log("IPA_ADD_USER", settings.IPA_LOG_FILE)
				self.ipa.login(settings.IPA_ADMIN_USER, settings.IPA_ADMIN_PWD)
			except Exception as e:
				self.logger.error("FreeIPA Connection Error - %s", e)
				self.ERR_MJR_MAIL += "Error occured in FreeIPA Connection - " + str(e) + "\n"
				self.err_mjr_cnt  += 1
				sendMail(self.ERR_MJR_MAIL, settings.FROM_ADDRS, settings.DCACHE_ADMIN_MAIL, settings.LDAP_SUBJECT)
				sys.exit(1)

			# Call to addUpdateProjects() Function
			if all_projects:
				# Assigning the all_projects from supr_swestore_main
				self.all_projects = all_projects
				self.addUpdateProjects()

			# Call to updateDeleteProjects() Function
			if persons_modified:
				# Assigning the persons_modified from supr_swestore_main
				self.persons_modified = persons_modified
				self.updateDeletePersons()

			# Call to sendMail() Function
			if self.err_mjr_cnt:
				self.msgtext += str(self.ERR_MJR_MAIL) + "\n"
			if self.err_proj_cnt:
				self.msgtext += str(self.ERR_PROJ_MAIL) + "\n"
			if self.err_pers_cnt:
				self.msgtext += str(self.ERR_PERS_MAIL) + "\n"
			if self.add_proj_cnt:
				self.msgtext += str(self.ADD_PROJ_MAIL) + "\n"
			if self.mod_proj_cnt:
				self.msgtext += str(self.MOD_PROJ_MAIL) + "\n"
			if self.add_pers_cnt:
				self.msgtext += str(self.ADD_PERS_MAIL) + "\n"
			if self.mod_pers_cnt:
				self.msgtext += str(self.MOD_PERS_MAIL) + "\n"
			if self.msgtext:
				sendMail(self.msgtext, settings.FROM_ADDRS, settings.DCACHE_ADMIN_MAIL, settings.LDAP_SUBJECT)

			# Call to function to create iRODS Users and Projects
			if self.irods_projects:
					self.irods_projects.sort(key = lambda p: p.id)
					supr_irods_pirc.SUPR_IRODS(self.irods_projects, [])


	# Mail to be to be sent to User for FreeIPA
	def sendIPAMail(self,m):

		msgTxt  = msgTxt  = "Dear " + m.first_name + " " + m.last_name + ",\n \n"
		#msgTxt += "You are receiving this mail as you are added as a member to Swestore project -- " + proj_name + " in SUPR. \n\n"
		msgTxt += "To set password to access Swestore/dCache or Swestore/iRods, login to portal - http://auth1.swestore.se/ipa/supr/supr-auth1.cgi \n"
		msgTxt += "First time, you will be redirected to SUPR for confirmation and then you can set a password which you can use to login to Swestore/iRods \n"
		msgTxt += "To know more on how to set password in IPA please refer to the following links :- \n"

		msgTxt += "http://snicdocs.nsc.liu.se/wiki/Swestore#Using_Swestore \n\n"

		msgTxt += "In case of any issues or clarifications, please mail support@swestore.se. \n\n"
		msgTxt += "Regards,\n" + "Swestore Support Team"

		sendMail(msgTxt, 'support@swestore.se', m.email, "Information to access Swestore")


	# Mail to be to be sent to User
	def sendUserMail(self,m, proj_name, sua_accepted):

		msgTxt  = "Dear " + m.first_name + " " + m.last_name + ",\n \n"
		msgTxt += "You are receiving this mail as you are added as a member to Swestore project -- " + proj_name + " in SUPR. \n \n"

		if not sua_accepted:
			msgTxt += "We have noticed that you have not signed the SNIC User Agreement.\n"
			msgTxt += "Before access to Swestore is granted, the SNIC User Agreement must be read and accepted.\n"
			msgTxt += "Login to SUPR (https://supr.snic.se/login), go to Personal Information and sign the SNIC User Agreement using Federated Identity. \n\n"
		else:
			if not m.subject:
				msgTxt += "Please register your eScience client certificate in SUPR as this is mandatory to authenticate and use Swestore/dCache .\n"
				msgTxt += "Login to SUPR (https://supr.snic.se/login), go to Personal Information, click Register Client Certificate and follow the instructions.\n"
				msgTxt += "Please wait for up to 10 minutes for this information to be distributed to Swestore. \n\n"
			msgTxt += "To know more on how to access Swestore, please refer to the following links :- \n"
			msgTxt += "http://snicdocs.nsc.liu.se/wiki/Swestore \n"
			msgTxt += "http://snicdocs.nsc.liu.se/wiki/Swestore#Using_Swestore \n\n"

		msgTxt += "In case of any issues or clarifications, please mail support@swestore.se. \n\n"
		msgTxt += "Regards,\n" + "Swestore Support Team"

		sendMail(msgTxt, 'support@swestore.se', m.email, "Information to access Swestore")


	# Generate userId or uid for new Person from first name and last name
	# using various combinations
	def getUID(self,m):
		guesses   = []
		firstname = ((m.first_name).replace(" ", "")).lower()
		lastname  = (m.last_name).replace(" ", "").lower()

		if len(firstname) < 3 and len(lastname) < 3:
			uid = "s_" + asciify(u'' + firstname + lastname)
			guesses.append(str(uid))
		else:
			for (flen, llen, swap) in ((3,2, False),
						   (2,3, False),
						   (3,2, True),
						   (2,3, True),
						   (1,4, False),
						   (4,1, False),
						   (1,4, True),
						   (4,1, True),   
						   (0,5, False),
						   (5,0, False),
						  ):
				if len(firstname) < flen or len(lastname) < llen:
					continue
				if swap:
					uid = "s_" + asciify(u'' + lastname[:llen] + firstname[:flen])
					guesses.append(str(uid))
				else:
					uid = "s_" + asciify(u'' + firstname[:flen] + lastname[:llen])
					guesses.append(str(uid))

		# Check if the uid already exists in LDAP
		self.logger.debug("Person with SUPR ID :: %s login guesses -- %s ", m.id, guesses)

		for login in guesses:

			filter = "uid=" + login
			ldap_result_id = self.l.search(settings.peopleDN, self.searchScope, filter, self.retrievedAttrs)
			result_type, result_data = self.l.result(ldap_result_id, 0)

			if (result_data == []):
				return login

		# No guess possible
		return str(guesses[0]+m.id)

	# Function to search Person based on uidNumber
	def searchPerson(self,uidNumber):

		try:
			# Check if the member already exists in LDAP
			filter = "(uidNumber=" + uidNumber+")"

			ldap_result_id = self.l.search(settings.peopleDN, self.searchScope, filter, self.retrievedAttrs)
			result_type, result_data = self.l.result(ldap_result_id, 0)
			return result_data
		except ldap.LDAPError as le:
			self.logger.error("LDAP Error in searchPerson Module for %s :: %s", str(uidNumber), le)
			self.ERR_PERS_MAIL += "uidNumber :: " + str(uidNumber) +  "\t Module :: searchPerson \n" 
			self.err_pers_cnt  += 1
			return []

	# Function to search MemberUid based on uidNumber in Groups for SUP not signed persons
	def searchMemberUid(self,uidNumber):

		try:
			# Check if the member already exists in LDAP
			filter = "(memberUid=" + uidNumber+")"
			retrievedAttrs = ['gidNumber', 'resourceID']

			ldap_result_id = self.l.search(settings.groupsDN, self.searchScope, filter, retrievedAttrs)
			result_type, result_data = self.l.result(ldap_result_id)
			return result_data
		except ldap.LDAPError as le:
			self.logger.error("LDAP Error in searchMemberUid Module for %s :: %s", str(uidNumber), le)
			self.ERR_PERS_MAIL += "uidNumber :: " + str(uidNumber) +  "\t Module :: searchMemberUid \n" 
			self.err_pers_cnt  += 1
			return []


	# Function to create Person Attributes 
	def createPersonAttrs(self,m,uidNumber):

		attrsPerson = {}
		attrsPerson['objectclass']      = ['Swestore','inetorgperson','posixaccount']
		attrsPerson['description']      = str(m.id)
		attrsPerson['uidNumber']        = uidNumber
		attrsPerson['gidNumber']        = uidNumber
		attrsPerson['gn']               = str((m.first_name).encode('utf-8'))
		attrsPerson['sn']               = str((m.last_name).encode('utf-8'))
		attrsPerson['cn']               =  str((m.first_name + " " + m.last_name).encode('utf-8'))
		attrsPerson['mail']             = str((m.email).encode('utf-8'))
		attrsPerson['subject']          = str((m.subject).encode('utf-8'))
		attrsPerson['lastModifiedTime'] = str(m.modified)
		attrsPerson['homeDirectory']    = "/"

		# Will be updated to the correct yubikey value once yubikey is integrated into SUPR
		attrsPerson['yubikey']          = "yubikey"

		# Need to check if centre_person_id comes from SUPR. If it clashes with other UIDs
		# then an alert mail needs to be sent to Admin about the same.
		if m.centre_person_id:
			attrsPerson['uid']      = str(m.centre_person_id)
		else:
			attrsPerson['uid']      = self.getUID(m)

		return attrsPerson

	# Function to check Person Data has changed
	def personChanged(self,result_data, attrsPerson):

		if(result_data[0][1].get('description',False) and result_data[0][1].get('description', '')[0] != attrsPerson['description']):
			return True
		if(result_data[0][1].get('givenName',False) and result_data[0][1].get('givenName','')[0] != attrsPerson['gn']):
			return True
		if(result_data[0][1].get('sn',False) and result_data[0][1].get('sn', '')[0] != attrsPerson['sn']):
			return True
		if(result_data[0][1].get('cn',False) and result_data[0][1].get('cn', '')[0] != attrsPerson['cn']):
			return True
		if(result_data[0][1].get('mail',False) and result_data[0][1].get('mail', '')[0] != attrsPerson['mail']):
			return True
		if((result_data[0][1].get('subject') == None and attrsPerson['subject']) or 
		   (result_data[0][1].get('subject') and result_data[0][1].get('subject', '')[0] != attrsPerson['subject'])):
                        return True
		if(result_data[0][1].get('uid',False) and result_data[0][1].get('uid', '')[0] != attrsPerson['uid']):
			return True

		return False

	# Function to add new Person
	def addPerson(self,m,uidNumber,resourceIDList):

		try:
			attrsPerson = self.createPersonAttrs(m,uidNumber)
			#personDN = "uidNumber=" + uidNumber + "," + peopleDN
			personDN = "uid=" + attrsPerson['uid'] + "," + settings.peopleDN

			ldif = modlist.addModlist(attrsPerson)
			self.l.add_s(personDN,ldif)

			self.logger.info("Person with SUPR ID :: %s added to LDAP -- %s", m.id, str(uidNumber))

			self.ADD_PERS_MAIL += "SUPR ID :: " +  str(m.id) + "\t username(uid) :: " + attrsPerson['uid'] +  "\t Person Name :: " + attrsPerson['cn'] + "\n"
			self.add_pers_cnt  += 1

			if m.centre_person_id:
				self.logger.info("Person with SUPR ID :: %s centre_person_id already exists -- %s", m.id, m.centre_person_id)
			else:
				# Updating the centre_person_id, uidNumber, gidNumber to SUPR
				d = {'centre_person_id' : attrsPerson['uid']}

				try:
					person = self.supr_connection.post("person/%s/update/" % m.id, data = d)
					m.centre_person_id = attrsPerson['uid']
					self.logger.info("Centre_Person_id for Person with SUPR ID :: %s updated to SUPR -- %s", m.id, attrsPerson['uid'])
				except supr.SUPRHTTPError as e:
					# We want to show the text received if we get an HTTP Error
					self.logger.error("HTTP error in updating data to SUPR - %s :: %s" % e.status_code  % e.text)
					self.ERR_MJR_MAIL += "Error occured in updating centre_person_id (uid) to SUPR - " + e.text + "\n"
					self.ERR_MJR_MAIL += "SUPR ID :: " +  str(m.id) + "\t username(uid) :: " + attrsPerson['uid'] +  "\t Person Name :: " + attrsPerson['cn'] + "\t Module :: addPerson \n"
					self.err_mjr_cnt  += 1
				except ConnectionError as ce:
					self.ERR_MJR_MAIL += "Error occured in updating centre_person_id (uid) to SUPR due to ConnectionError- " + str(ce) + "\n"
					self.logger.error("Connection to SUPR failed - %s" %str(ce))

			for resourceid in resourceIDList:
				d = {'username' : m.centre_person_id, 
				     'person_id' : m.id,
				     'resource_id' : resourceid,
				     'status' : 'enabled'}
				try:
					account = self.supr_connection.post("account/create/", data = d)
					self.logger.info("Account for Person with SUPR ID :: %s for resource -- %s created", m.id, resourceid)
				except supr.SUPRHTTPError as e:
					# We want to show the text received if we get an HTTP Error
					self.logger.error("HTTP error in creating account to SUPR - %s :: %s", e.status_code, e.text)
					self.ERR_MJR_MAIL += "Error occured in creating account to SUPR - " + e.text + "\n"
					self.ERR_MJR_MAIL += "SUPR ID :: " +  str(m.id) + "\t username(uid) :: " + str(attrsPerson['uid']) + "\t Module :: addPerson \n"
					self.err_mjr_cnt  += 1
				except ConnectionError as ce:
					self.ERR_MJR_MAIL += "Error occured in creating account to SUPR due to ConnectionError- " + str(ce) + "\n"
					self.logger.error("Connection to SUPR failed - %s" %str(ce))
			

			# Adding Project for every Person
			self.addPersonAsProject(attrsPerson)
			
			# Adding Person to FreeIPA
			self.addPersontoFreeIPA(m,attrsPerson)

		except ldap.LDAPError as le:
			self.logger.error("LDAP Error in addPerson Module for %s :: %s", str(uidNumber), le)
			self.ERR_PERS_MAIL += "uidNumber :: " + str(uidNumber) +  "\t Module :: addPerson \n"
			self.err_pers_cnt  += 1


	# Function to add new person to ipa
	def addPersontoFreeIPA(self,m,attrsPerson):

		length = 13
		chars = string.ascii_letters + string.digits + '!@#$%^&*()'
		random.seed = (os.urandom(1024))
		tmp_password = ''.join(random.choice(chars) for i in range(length))

		try:
			user = attrsPerson['uid']
			opts = {"givenname": attrsPerson['gn'], 
			        "sn": attrsPerson['sn'], 
			        "mail" : attrsPerson['mail'], 
			        "uidnumber":attrsPerson['uidNumber'],
			        "userpassword":tmp_password, # uncomment when ipa goes to production
			        }
			result = self.ipa.user_add(user, opts)
			self.sendIPAMail(m)

		except Exception as e:
			self.logger.error("Error in addPersontoFreeIPA Module for %s :: %s", str(attrsPerson['uid']), e)
			self.ERR_PERS_MAIL += "uidNumber :: " + str(attrsPerson['uid']) +  "\t Module :: addPersontoFreeIPA \n"
			self.err_pers_cnt  += 1


	# Function to update Person Data or delete merged Persons
	def updateDeletePersons(self):

		gidNumbers = None
		try:
			for m in self.persons_modified:

				uidNumber   = str(settings.uidNumberStart + m.id)
				result_data = self.searchPerson(uidNumber)

				if(result_data == []):
					# Kris : Add code here to check for uidnumber in memberUids in groups
					gidNumbers = self.searchMemberUid(uidNumber)
					if not gidNumbers == []:
						if m.user_agreement_version and m.user_agreement_accepted:

							for gidNumber in gidNumbers:
								# Kris Add code here.
								
								gid = gidNumber[1].get('gidNumber')[0]
								resourceIDList = gidNumber[1].get('resourceID')

								groupDN = "gidNumber=" + gid + "," + settings.groupsDN
								oldMemberUid = {'memberUid':_[uidNumber]}
								newMemberUid = {'memberUid': [m.centre_person_id]}
								ldif = modlist.modifyModlist(oldMemberUid,newMemberUid)
								self.l.modify_s(groupDN,ldif)
							
								self.addPerson(m,uidNumber,resourceIDList)

							self.logger.info("Person with SUPR ID :: %s SUP is signed and will be updated to LDAP.", m.id)

					else:
						self.logger.info("Person with SUPR ID :: %s not needed in LDAP. Just ignore it.", m.id)
				else:

					for merge_id in m.merged_ids:
						mergeUidNumber   = str(settings.uidNumberStart + merge_id)
						result_data_mrg  = self.searchPerson(mergeUidNumber)

						if(result_data_mrg == []):
							self.logger.info("Person with SUPR ID :: %s has already been deleted from LDAP since its merged with SUPR ID :: %s ", merge_id, m.id)
						else:
							personDN = "uid=" + result_data_mrg[0][1].get('uid')[0] + "," + settings.peopleDN
							groupDN  = "gidNumber=" + mergeUidNumber + "," + settings.groupsDN

							self.l.delete_s(personDN)
							self.logger.info("Person with SUPR ID :: %s deleted from LDAP since its merged with SUPR ID :: %s ", merge_id, m.id)

							self.MOD_PERS_MAIL += "SUPR Person ID :: " + str(merge_id) + " merged with SUPR Person ID :: " +  str(m.id) + "\n"
							self.mod_pers_cnt  += 1

							# Deleting the corresponding Project as well
							self.l.delete_s(groupDN)
							self.logger.info("Project with ID :: %s deleted from LDAP since its person is also deleted :: %s ",  merge_id, merge_id)

					attrsPerson = self.createPersonAttrs(m,uidNumber)

					#personDN = "uidNumber=" + uidNumber + "," + peopleDN

					personDN = "uid=" + attrsPerson['uid'] + "," + settings.peopleDN

					if(self.personChanged(result_data,attrsPerson)):
						self.l.delete_s(personDN)
						ldif = modlist.addModlist(attrsPerson)
						self.l.add_s(personDN,ldif)
						self.logger.info("Person with SUPR ID :: %s modified to LDAP -- %s", m.id, attrsPerson['uidNumber'])

						self.MOD_PERS_MAIL += "SUPR ID :: " +  str(m.id) +  "\t username(uid) :: " + attrsPerson['uid'] + "\t Person Name :: " + attrsPerson['cn'] + "\n"
						self.mod_pers_cnt  += 1

					else:
						self.logger.info("Person with SUPR ID :: %s - No changes since last time", m.id)
			
		except ldap.LDAPError as le:
			self.logger.error("LDAP Error in updateDeletePersons Module for %s :: %s", str(uidNumber), le)
			self.ERR_PERS_MAIL += "uidNumber :: " + str(uidNumber) +  "\t Module Name :: updateDeletePerson \n"
			self.err_pers_cnt  += 1

	# Function to search Project based on gidNumber
	def searchProject(self,gidNumber,cn):

		try:
			# Check if the project already exists in LDAP
			filter = "(|(gidNumber=" + gidNumber + ")(cn=" + cn + "))"

			ldap_result_id = self.l.search(settings.groupsDN, self.searchScope, filter, self.retrievedAttrs)
			result_type, result_data = self.l.result(ldap_result_id, 0)
			return result_data
		except ldap.LDAPError as le:
			self.logger.error("LDAP Error in searchProject Module for %s :: %s", str(gidNumber), le)
			self.ERR_PROJ_MAIL += "gidNumber :: " + str(gidNumber) +  "\t Module :: searchProject \n" 
			self.err_proj_cnt  += 1
			return []

	# Function to add / update Projects
	def addUpdateProjects(self):

		for p in self.all_projects:

			attrsGroup     = {}
			memberUIDList  = []
			resourceIDList = []
			#resourceList   = []
                        sua_accepted = None

			for rp in p.resourceprojects:
				resourceIDList.append(str(rp.resource.id))

				#resourceList.append(rp.resource)

			for m in p.members:
				# Generate uidNumber for new Person 
				# ( Example 30023 - 30000 is the start range and 23 is the person id from SUPR )
				uidNumber = str(settings.uidNumberStart + m.id)
				result_data = self.searchPerson(uidNumber)

				if(result_data == []):
					if m.user_agreement_version and m.user_agreement_accepted:
						self.addPerson(m,uidNumber,resourceIDList)
						sua_accepted = True

						# To send user mail regarding user certificate registration in SUPR for dcache projects
						if settings.dcache_resource_id in resourceIDList:
							self.sendUserMail(m, p.name, sua_accepted)
						self.logger.info("Person with SUPR ID :: %s SUP is signed and will be added to LDAP.", m.id)
					else:
						sua_accepted = False
						# To send user mail regarding SUA in SUPR for all projects
						self.sendUserMail(m, p.name, sua_accepted)
						self.logger.info("Person with SUPR ID :: %s SUP is not signed and will not be added to LDAP.", m.id)
						
						# Kris : Add UidNumber as MemberUid in Group fo SUP not signed
						m.centre_person_id = uidNumber
				else:
					if(result_data[0][1].get('uid')[0]):
						m.centre_person_id = result_data[0][1].get('uid')[0]
						#self.sendIPAMail(m)

					self.logger.info("Person with SUPR ID :: %s - Already added to LDAP \n", m.id)

				memberUIDList.append(str(m.centre_person_id))

			if settings.irods_resource_id in resourceIDList:
				self.irods_projects.append(p)

			# Generate gidNumber for new Project 
			# ( Example 6012 - 6000 is the start range and 12 is the project id from SUPR )	
			gidNumber = str(settings.gidNumberStart + p.id)

			groupDN = "gidNumber=" + gidNumber + "," + settings.groupsDN
			attrsGroup['objectclass']      = ['Swestore','posixgroup']
			attrsGroup['description']      = [str(p.id)]
			attrsGroup['piMemberID']       = str(settings.uidNumberStart + p.pi.id)
			attrsGroup['memberUID']        = memberUIDList
			attrsGroup['resourceID']       = resourceIDList
			attrsGroup['projectEndDate']   = str(p.end_date)
			attrsGroup['lastModifiedTime'] = str(p.modified)

			if p.directory_name:
				attrsGroup['cn'] = str((p.directory_name).encode('utf-8'))

			try:
				result_data = self.searchProject(gidNumber, attrsGroup['cn'])

				# Load data into LDAP
				if (result_data == []):
					ldif = modlist.addModlist(attrsGroup)
					self.l.add_s(groupDN,ldif)
					self.logger.info("Project with SUPR ID :: %s added to LDAP -- %s \n", p.id, gidNumber)

					self.ADD_PROJ_MAIL += "SUPR ID :: " +  str(p.id) + "\t Project Name :: " + p.directory_name + "\t Persons Added :: " + ", ".join(memberUIDList) + "\n"
					self.add_proj_cnt  += 1

				else:
					if (result_data[0][1]['lastModifiedTime'][0] != attrsGroup['lastModifiedTime']):

						addUsers    = list(set(memberUIDList).difference(set(result_data[0][1]['memberUid'])))
						removeUsers = list(set(result_data[0][1]['memberUid']).difference(set(memberUIDList)))
						suprIds     = result_data[0][1]['description']

						if p.continuation_name:
							gidNumber = result_data[0][1]['gidNumber'][0]
							groupDN   = "gidNumber=" + gidNumber + "," + settings.groupsDN
							attrsGroup['description']  = suprIds + [str(p.id)]

						self.l.delete_s(groupDN)
						ldif = modlist.addModlist(attrsGroup)
						self.l.add_s(groupDN,ldif)

						self.logger.info("Project with SUPR ID :: %s modified to LDAP -- %s ", p.id, gidNumber)

						if p.continuation_name:
							self.MOD_PROJ_MAIL += "SUPR ID :: " +  str(p.id) + "\t Project Name :: " + attrsGroup['cn'] + "\t Continuation project for SUPR ID(s) :: " +  ", ".join(suprIds) + "\n"
							self.mod_proj_cnt  += 1

						newCn = False
						if attrsGroup['cn'] != result_data[0][1]['cn'][0]:
							self.MOD_PROJ_MAIL += "SUPR ID :: " +  str(p.id) + "\t New Project Name :: " + attrsGroup['cn'] + "\t Old Project Name :: " + result_data[0][1]['cn'][0]  + "\n"
							self.mod_proj_cnt  += 1
							newCn = True

						if removeUsers:
							self.MOD_PROJ_MAIL += "SUPR ID :: " +  str(p.id) + "\t Project Name :: " + attrsGroup['cn'] + "\t Persons Removed :: " + ", ".join(removeUsers) + "\n"
							self.mod_proj_cnt  += 1

						if addUsers:
							self.MOD_PROJ_MAIL += "SUPR ID :: " +  str(p.id) + "\t Project Name :: " + attrsGroup['cn'] + "\t Persons Added   :: " + ", ".join(addUsers) + "\n"
							self.mod_proj_cnt  += 1

						if not (removeUsers or addUsers or p.continuation_name or newCn):
							self.MOD_PROJ_MAIL += "SUPR ID :: " +  str(p.id) + "\t Project Name :: "  + attrsGroup['cn'] + "\n"
							self.mod_proj_cnt  += 1

					else:
						self.logger.info("Project with SUPR ID :: %s - No changes since last time \n", p.id)

			except ldap.LDAPError as le:
				self.logger.error("LDAP Error in addUpdateProjects Module for %s :: %s", str(gidNumber), le)
				self.ERR_PROJ_MAIL += "gidNumber :: " + str(gidNumber) +  "\t Module :: addUpdateProjects \n"
				self.err_proj_cnt  += 1


	# For every Person add a corresponding Project with uidNumber as gidNumber
	def addPersonAsProject(self,attrsPerson):

		attrsGroup = {}
		attrsGroup['cn'] = attrsPerson['uid']
		attrsGroup['description'] = attrsPerson['description']
		attrsGroup['piMemberID'] = attrsPerson['uidNumber']
		attrsGroup['memberUID'] = [attrsPerson['uid']]
		attrsGroup['objectclass'] = ['Swestore','posixgroup']

		gidNumber = attrsPerson['uidNumber']
		attrsGroup['gidNumber'] = gidNumber
		groupDN = "gidNumber=" + gidNumber + "," + settings.groupsDN

		try:
			result_data = self.searchProject(gidNumber, attrsGroup['cn'])

			# Load data into LDAP
			if (result_data == []):
				ldif = modlist.addModlist(attrsGroup)
				self.l.add_s(groupDN,ldif)
				self.logger.info("Project with ID :: %s added to LDAP -- %s \n", attrsPerson['description'], attrsGroup['gidNumber'])

			else:
				self.logger.info("Project with ID :: %s - already added", attrsPerson['description'])

		except ldap.LDAPError as le:
			self.logger.error("LDAP Error in addPersonAsProject Module for %s :: %s", str(gidNumber), le)
			self.ERR_PROJ_MAIL += "gidNumber :: " + str(gidNumber) +  "\t Module :: addPersonAsProject \n"
			self.err_proj_cnt  += 1
