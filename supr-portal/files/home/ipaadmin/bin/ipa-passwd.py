#!/bin/python

#! -*- coding: utf-8 -*-

# Change password for an IPA user.
# Arguments:
#     Center Person ID, which is the same as the IPA userid.
#     Password

# System definitions.
import os
import sys
import re
import subprocess

# Arguments:
#     Center Person ID, which is the same as the IPA userid.
#     Password
#     Verification
# Returns status code. Message text won't be passed up.

# Run command.

def run(cmd, args=None, input=None, cwd=None, env=None):

    # Create command. Note: Exactly one blank between the parts.
    c = cmd.split(' ')

    # Add the arguments.
    if args is not None:
        for a in args:
            c.append(a)

    # Add dictionary content to environment as specified.
    if env is not None:
        e = dict(os.environ)
        e.update(env)
    else:
        e = None

    # Open the pipe.
    try:
        p = subprocess.Popen(c, cwd=cwd, env=e,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False, bufsize=0)
    except:
        return None

    # Send input if any and finish with subprocess.
    try:
        (out, err) = p.communicate(input=input)
    except:
        return None

    # Went trhough the motions but there was an error.
    if p.returncode != 0:
        return (out, err)

    # Finish and return output.
    return (out, err)


# Get arguments and check. Need to have two arguments.
if len(sys.argv) != 3:
    sys.exit(1)

# Check for the user. Should look like a Swestore user.
user = sys.argv[1]
if not re.match('s_', user):
    sys.exit(1)

# Get password and check if unreasonable.
password = sys.argv[2]
if len(password) > 256:
    sys.exit(1)

# Password change input to pass to kadmin.
kp = "cpw " + user + "\n" + password + '\n' + password + '\n'

# Kerberos kadmin command.
kadmin_command = '/bin/kadmin -p ipaadmin/changepw@SWESTORE.SE -k -t /home/ipaadmin/keys/ipaadmin-changepw.keytab -s 127.0.0.1 -x ipa-setup-override-restrictions'

r = run (kadmin_command, input=kp, cwd='/home/ipaadmin', env=dict())
if r is None:
    sys.exit(1)
(out, err) = r

# Debug.
#print '>>>> stdout'
#print out
#print '>>>> stderr'
#print err
#print '>>>> finish'

# Finish.
sys.exit(0)

