#!/usr/bin/python
#! -*- coding: utf-8 -*-

import logging
import smtplib
import os, random, string

from email.mime.text import MIMEText
from email.header import Header
from unicodedata import decomposition

from settings import (LOG_FILE,
		      LOG_FILE_FORMAT,
		      LOG_FILE_DATEFORMAT,
		      SMTP_HOST,
		      SMTP_PORT,
		     )

# Function to convert non ascii characters to ascii.
# This is used for creating user IDs (uids)
def asciify(string):
	# ASCIIfy
	u2a = {
		u'æ' : u'ae',
		u'Æ' : u'AE',
		u'ø' : u'o',
		u'Ø' : u'O',
		u'ß' : u'ss',
		u'þ' : u'th',
		u'ð' : u'd',
		u'´' : u"'"
		}

	'''"ASCIIfy" a Unicode string by stripping all umlauts, tildes, etc.'''
	temp = u''
	for char in string:
		# Special case a few characters that don't decompose
		if char in u2a:
			temp += u2a[char]
			continue

		decomp = decomposition(char)
		if decomp: 
			temp += unichr(int(decomp.split()[0], 16))
		else: 
			temp += char
	return temp

# Function to setup Log Functionality for each module or Class
# Individual classes can configure accordingly
def setup_log(logger_name, log_file, level=logging.INFO):
	# logging configuration
	#logging.basicConfig(level=logging.INFO,
        #            format=LOG_FILE_FORMAT,
        #            datefmt=LOG_FILE_DATEFORMAT,
        #            stream=log_file,
        #            filemode='w')

	logger    = logging.getLogger(logger_name)

	hdlr      = logging.FileHandler(log_file)
	formatter = logging.Formatter(LOG_FILE_FORMAT, LOG_FILE_DATEFORMAT)
	hdlr.setFormatter(formatter)
	logger.setLevel(level)
	logger.addHandler(hdlr)

	return logger

# logging configuration
log_main = setup_log('SUPR_COMMON', LOG_FILE)

# Function to send mail to Admins for daily logs and other important errors.
def sendMail(msgtext, from_address, to_address, subject):

	if msgtext:
		msg = MIMEText(msgtext, 'plain', 'utf-8')
		msg['Subject'] = Header(subject, 'utf-8')
		msg['From'] = from_address
		msg['To'] = to_address

		# Send the message via our own SMTP server
		s = None
		try:
			s = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
			#s.starttls()
			s.sendmail(from_address, to_address, msg.as_string())

		except smtplib.SMTPException as se:
			log_main.error("SMTP Error in Sending Mail - %s", se)
		finally:
			if s:
				s.quit()


# Function to get generate temporary password
def temp_password():
	length = 13
	chars = string.ascii_letters + string.digits + '!@#$%^&*()'
	random.seed = (os.urandom(1024))
	tmp_password = ''.join(random.choice(chars) for i in range(length))
	return tmp_password
