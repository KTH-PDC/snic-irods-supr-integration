#!/usr/bin/python
#! -*- coding: utf-8 -*-

import logging
import sys
import settings
from irods.session import iRODSSession
from irods.access import iRODSAccess
from irods.exception import *

from supr_common import (sendMail,
			 setup_log)

class SUPR_IRODS:

	def __init__(self, irods_projects, irods_persons_modified):

		if irods_projects or irods_persons_modified:

			# Setting irods_projects
			self.irods_projects      = irods_projects
			self.sess		 = None

			# Get Logging File Handler
			self.logger              = setup_log(self.__class__.__name__, settings.IRODS_LOG_FILE)

			# Variables needed for calculating number of projects and persons created 
			# that are used to sendMail to Admins
			self.add_proj_cnt        = 0
			self.err_proj_cnt        = 0
			self.add_grp_cnt         = 0
			self.mod_grp_cnt         = 0
			self.err_grp_cnt         = 0  
			self.err_grp_mod_cnt     = 0
			self.add_pers_cnt        = 0
			self.err_pers_cnt        = 0
			self.sua_pers_cnt        = 0
			self.err_mjr_cnt         = 0

			# Variables needed for Message Text of projects and persons created 
			# that are used to sendMail to Admins
			self.ADD_PERS_MAIL      = "The Following Persons have been Added on " + settings.today + "\n" 
			self.ADD_PERS_MAIL     += "---------------------------------------------------- \n"

			self.SUA_PERS_MAIL      = "The Following Persons have not signed SUA and hence not added on " + settings.today + "\n" 
			self.SUA_PERS_MAIL     += "---------------------------------------------------- \n"


			self.ADD_PROJ_MAIL      = "The Following Projects have been Added on " + settings.today + "\n" 
			self.ADD_PROJ_MAIL     += "----------------------------------------------------- \n"

			self.ADD_GRP_MAIL       = "The Following Groups have been Added on " + settings.today + "\n" 
			self.ADD_GRP_MAIL      += "----------------------------------------------------- \n"

			self.MOD_GRP_MAIL       = "The Following Groups have been Modified on " + settings.today + "\n" 
			self.MOD_GRP_MAIL      += "----------------------------------------------------- \n"

			self.ERR_PROJ_MAIL      = "Error in creating the following Projects on " + settings.today + "\n" 
			self.ERR_PROJ_MAIL     += "------------------------------------------------------- \n"

			self.ERR_GRP_MAIL       = "Error in creating the following Groups on " + settings.today + "\n"
			self.ERR_GRP_MAIL      += "---------------------------------------------------- \n"

			self.ERR_GRP_MOD_MAIL   = "Error in modifying the following Groups on " + settings.today + "\n"
			self.ERR_GRP_MOD_MAIL  += "---------------------------------------------------- \n"

			self.ERR_PERS_MAIL      = "Error in creating the following Persons on " + settings.today + "\n" 
			self.ERR_PERS_MAIL     += "------------------------------------------------------- \n"

			self.ERR_MJR_MAIL       = "Major Error Occured on " + settings.today + "\n" 
			self.ERR_MJR_MAIL      += "---------------------------------- \n"

			self.msgtext = ""

			# Call to AddProjects Function
			if irods_projects:
				self.addProjects()

			# Call to sendMail() Function
			if self.err_mjr_cnt:
				self.msgtext += str(self.ERR_MJR_MAIL) + "\n"
			if self.err_pers_cnt:
				self.msgtext += str(self.ERR_PERS_MAIL) + "\n"
			if self.err_proj_cnt:
				self.msgtext += str(self.ERR_PROJ_MAIL) + "\n"
			if self.err_grp_cnt:
				self.msgtext += str(self.ERR_GRP_MAIL) + "\n"
			if self.err_grp_mod_cnt:
				self.msgtext += str(self.ERR_GRP_MOD_MAIL) + "\n"
			if self.add_proj_cnt:
				self.msgtext += str(self.ADD_PROJ_MAIL) + "\n"
			if self.add_grp_cnt:
				self.msgtext += str(self.ADD_GRP_MAIL) + "\n"
			if self.add_pers_cnt:
				self.msgtext += str(self.ADD_PERS_MAIL) + "\n"
			if self.sua_pers_cnt:
				self.msgtext += str(self.SUA_PERS_MAIL) + "\n"
			if self.mod_grp_cnt:
				self.msgtext += str(self.MOD_GRP_MAIL) + "\n"
			if self.msgtext:
				sendMail(self.msgtext, settings.FROM_ADDRS, settings.IRODS_ADMIN_MAIL, settings.IRODS_SUBJECT)

	# Function to add Users in irods and Assign Users to Groups
	def addUser(self,m,proj_name,addUsers,cantAddUsers):

		uidNumber = str(settings.uidNumberStart + m.id)

		if m.centre_person_id and not (m.centre_person_id == uidNumber):

			userName = str(m.centre_person_id).strip()
			certi_subj = "";

			if m.subject and not m.subject == "":
				certi_subj = str((m.subject).encode('utf-8'))
			try:
				user     = self.sess.users.get(userName)

				if not certi_subj == "":

					if user.dn:
						self.sess.users.modify(userName, 'rmAuth', user.dn[0])

					self.sess.users.modify(userName, 'addAuth', certi_subj)

					self.logger.info(userName + " certificate added to irods auth")
				self.logger.info(userName + " user already exists")
				newUser = False

			except UserDoesNotExist:
				try:
					user     = self.sess.users.create(userName, "rodsuser")
					self.logger.info(userName + " user created")
					
					if not certi_subj == "":
						self.sess.users.modify(userName, 'addAuth', certi_subj)
						self.logger.info(userName + " certificate added to irods auth")


					newUser = True
					self.ADD_PERS_MAIL += "SUPR ID :: " +  str(m.id) + "\t username(uid) :: " + userName +  "\t Person Name :: " + str((m.first_name).encode('utf-8')) + " " + str((m.last_name).encode('utf-8')) + "\n"
					self.add_pers_cnt  += 1

				except Exception as e:
					self.logger.error(str(m.centre_person_id) + " user could not be created due to " + repr(e))
					self.ERR_PERS_MAIL += "SUPR ID :: " +  str(m.id) + "\t username(uid) :: " + userName +  "\t Person Name :: " + str((m.first_name).encode('utf-8')) + " " + str((m.last_name).encode('utf-8')) + "\n"
					self.err_pers_cnt  += 1

			group = self.sess.user_groups.get(proj_name)
			if group:
				# Add the users to the group
				if user:
					if group.hasmember(userName):
						self.logger.info(userName + " user already exists in " + proj_name + " group")
					else:
						try:
							group.addmember(userName)
							addUsers.append(userName)
							self.logger.info(userName + " user added to " + proj_name + " group")
							self.sendUserMail(m, proj_name, newUser)
						except Exception as e:
							cantAddUsers.append(userName)
							self.logger.error(userName + " user could not be added to " + proj_name + " group due to " + repr(e))

				else:
					cantAddUsers.append(userName)
					self.logger.error(userName + " user was not created. Hence could not be added to " + proj_name)

			else:
				self.logger.error(proj_name + " group does not exist")

			userGroup  = self.sess.user_groups.get("users")
			if userGroup:
				# Add the users to the usergroup
				if userGroup.hasmember(userName):
					self.logger.info(userName + " user already exists in users group \n")

				else:
					userGroup.addmember(userName)
					self.logger.info(userName + " user added to users group \n")
			else:
				self.logger.error("users group does not exist")
				self.ERR_GRP_MAIL += "users group does not exist \n"
				self.err_grp_cnt  += 1


	# Function to add Projects and Users and Assign Users to Groups
	def addProjects(self):
		coll = None
		group = None

		try:

			# Connection to a server with the default values
			self.sess = iRODSSession(host=settings.IRODS_HOST, 
					    port=settings.IRODS_PORT, 
					    user=settings.IRODS_ADMIN_USER, 
					    password=settings.IRODS_ADMIN_PWD, 
					    zone=settings.IRODS_ZONE)

			try:
				c = self.sess.collections.get(settings.IRODS_DIR)
				self.logger.info("Client Connection to iRODS successful \n")
			except CollectionDoesNotExist:
				try:
					c = self.sess.collections.create(settings.IRODS_DIR)
				except Exception as e:
					self.logger.error(settings.IRODS_DIR + " could not be created due to " + repr(e))
					self.ERR_MJR_MAIL += settings.IRODS_DIR + " could not be created " + "\n"
					self.err_mjr_cnt  += 1

			try:
				userGroup  = self.sess.user_groups.get("users")
			except UserGroupDoesNotExist:
				try:
					userGroup  = self.sess.user_groups.create("users")
				except Exception as e:
					self.logger.error(" users group could not be created due to " + repr(e))
					self.ERR_MJR_MAIL += " users group could not be created " + "\n"
					self.err_mjr_cnt  += 1

			for p in self.irods_projects:

				proj_name = ((p.directory_name).encode('utf-8')).lower()

				# Creation of projects. It is created as collection
				try:
					coll = self.sess.collections.get(settings.IRODS_DIR + "/" + proj_name )
					self.logger.info(settings.IRODS_DIR + "/" + proj_name + " directory already exists")

				except CollectionDoesNotExist:
					try:
						coll = self.sess.collections.create(settings.IRODS_DIR + "/" + proj_name)
						self.logger.info(settings.IRODS_DIR + "/" + proj_name + " directory created")
						self.ADD_PROJ_MAIL += "SUPR ID :: " +  str(p.id) + "\t Project Name :: " + proj_name + "\n"
						self.add_proj_cnt  += 1

					except Exception as e:
						self.logger.error(settings.IRODS_DIR + proj_name + " directory could not be created due to " + repr(e))
						self.ERR_PROJ_MAIL += "SUPR ID :: " +  str(p.id) + "\t Project Name :: " + proj_name + "\n"
						self.err_proj_cnt  += 1

				# Creation of groups. It is created as group in PiRC
				try:
					group = self.sess.user_groups.get(proj_name)
					newGroup = False
					self.logger.info(proj_name + " group already exists \n")

				except UserGroupDoesNotExist:
					try:
						group    = self.sess.user_groups.create(proj_name)
						newGroup = True
						self.logger.info(proj_name + " group created \n")

					except Exception as e:
						self.logger.error(proj_name + " group could not be created due to " + repr(e))
						self.ERR_GRP_MAIL += "SUPR ID :: " +  str(p.id) + "\t Group Name :: " + proj_name + "\n"
						self.err_grp_cnt  += 1

				removedUsers    = []
				cantRemoveUsers = []

				# Remove the users from group that have been removed from project in SUPR
				if group:
					for groupuser in group.members:
						userName = str(groupuser.name)

						if userName not in (str(m.centre_person_id).strip() for m in p.members):

							try:
								group.removemember(userName)
								removedUsers.append(userName)
								self.logger.info(userName + " user removed from " + proj_name + " group")

							except Exception as e:
								cantRemoveUsers.append(userName)
								self.logger.error(userName + " user could not be removed from " + proj_name + " group due to :: " + repr(e))

				if removedUsers:
					self.MOD_GRP_MAIL += "SUPR ID :: " +  str(p.id) + "\t Group Name :: " + proj_name + "\t Persons Removed :: " + ", ".join(removedUsers) + "\n"
					self.mod_grp_cnt  += 1
				if cantRemoveUsers:
					self.ERR_GRP_MOD_MAIL += "SUPR ID :: " +  str(p.id) + "\t Group Name :: " + proj_name + "\t Persons Couldnot be Removed :: " + ", ".join(cantRemoveUsers) + "\n"
					self.err_grp_mod_cnt  += 1

				addUsers     = []
				cantAddUsers = []
				suaNotSigned = []
				for m in p.members:
					if m.user_agreement_version and m.user_agreement_accepted:
						self.addUser(m,proj_name,addUsers,cantAddUsers)
					else:
						suaNotSigned.append(str(m.id))

				if addUsers and not newGroup:
					self.MOD_GRP_MAIL += "SUPR ID :: " +  str(p.id) + "\t Group Name :: " + proj_name + "\t Persons Added   :: " + ", ".join(addUsers) + "\n"
					self.mod_grp_cnt  += 1

				if addUsers and newGroup:
					self.ADD_GRP_MAIL += "SUPR ID :: " +  str(p.id) + "\t Group Name :: " + proj_name + "\t Persons Added :: " + ", ".join(addUsers) + "\n"
					self.add_grp_cnt  += 1

				if cantAddUsers:
					self.ERR_GRP_MOD_MAIL += "SUPR ID :: " +  str(p.id) + "\t Group Name :: " + proj_name + "\t Persons Couldnot be Added :: " + ", ".join(cantAddUsers) + "\n"
					self.err_grp_mod_cnt  += 1

				if suaNotSigned:
					self.SUA_PERS_MAIL += "SUPR ID :: " +  str(p.id) + "\t Group Name :: " + proj_name + "\t Persons SUA Not signed :: " + ", ".join(suaNotSigned) + "\n"
					self.sua_pers_cnt  += 1

				# update the Ownership of the collection from admin to the group
				try:
					access = iRODSAccess("own", settings.IRODS_DIR + "/" + proj_name, proj_name, settings.IRODS_ZONE)
					self.sess.permissions.set(access,recursive=True)
					self.logger.info("Ownership added to " + proj_name + "\n")

				except Exception as e:
					self.logger.error("Ownership could not be added to " + proj_name + " due to " + repr(e))
					self.ERR_PROJ_MAIL += "SUPR ID :: " +  str(p.id) + "\t Ownership could not be added to Group :: " + proj_name + "\n"
					self.err_proj_cnt  += 1

				# update the Inheritance of the collection
				try:
					access = iRODSAccess("inherit", settings.IRODS_DIR+ "/" + proj_name, proj_name, settings.IRODS_ZONE)
					self.sess.permissions.set(access,recursive=True)
					self.logger.info("Inheritance enabled to " + proj_name + "\n")

				except Exception as e:
					self.logger.error("Inheritance could not be enabled to " + proj_name + " due to " + repr(e))
					self.ERR_PROJ_MAIL += "SUPR ID :: " +  str(p.id) + "\t Inheritance could not be added to Group :: " +  proj_name + "\n"
					self.err_proj_cnt  += 1

		except iRODSException as ie:
			self.logger.error("Error during iRODS Connection: %s", repr(ie))
			self.ERR_MJR_MAIL += "Error occured in iRODS Connection - " + repr(ie) + "\n"
			self.err_mjr_cnt  += 1
			sendMail(self.ERR_MJR_MAIL, settings.FROM_ADDRS, settings.IRODS_ADMIN_MAIL, settings.IRODS_SUBJECT)
			sys.exit(1)

		except Exception as e:
			self.logger.error("Error during iRODS Connection: %s", repr(e))
			self.ERR_MJR_MAIL += "Error occured in iRODS Connection - " + repr(e) + "\n"
			self.err_mjr_cnt  += 1
			sendMail(self.ERR_MJR_MAIL, settings.FROM_ADDRS, settings.IRODS_ADMIN_MAIL, settings.IRODS_SUBJECT)
			sys.exit(1)
		finally:
			if self.sess:
				self.sess.cleanup()

	# Message to be sent to User
	def sendUserMail(self, m, proj_name, newUser):

		msgTxt  = "Dear " + m.first_name + " " + m.last_name + ",\n \n"
		msgTxt += "You are receiving this mail as you are added as a member to Swestore/iRODS project -- " + proj_name + " in SUPR. \n\n"
		msgTxt += "Your username is " + str(m.centre_person_id) + "\n"
		msgTxt += "Your project path is " + settings.IRODS_DIR + "/" + proj_name + "\n \n"
		msgTxt += "The username is automatically generated using the firstname and lastname.\n"
                
                #if newUser:
			#msgTxt += "The yubikey would be posted to the address mentioned in the SUPR. \n \n"
		#else:
			#msgTxt += "Kindly use the yubikey that has been sent you earlier. \n \n"

		msgTxt += "For more information on connecting and using snic-irods,\n"
		msgTxt += "please refer to http://snicdocs.nsc.liu.se/wiki/Swestore-irods \n \n"
		msgTxt += "Regards,\n" + "Swestore/iRODS Support Team"

		sendMail(msgTxt, settings.IRODS_FROM_ADDRS, m.email, settings.IRODS_USR_SUBJECT)
