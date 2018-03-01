#!/bin/sh

# Change password for an IPA user.

# Arguments:
#     Center Person ID, which is the same as the IPA userid.
#     Password
#     Verification

# Get arguments and check.
U="$1"
case "$U" in
s_*)
	;;
fconagy|ilarik)
	;;
*)
	echo "Wrong userid"
	exit 1
	;;
esac
P="$2"

# Get/renew ticket. Credentials for IPA commands.
export KRB5CCNAME=FILE:/home/ipaadmin/keys/ipaadmin.krb5cc
kinit -l 10d -k -t /home/ipaadmin/keys/ipaadmin.keytab ipaadmin@SWESTORE.SE \
	>/dev/null 2>&1
if [ $? -eq 0 ]
then
	:
else
	echo "Authentication failed"
	exit 1
fi

# Find the user by userid.
TMP1=/home/ipaadmin/tmp/user.$$.tmp
ipa -n user-find --login="$U" >$TMP1 2>&1
if [ $? -ne 0 ]
then
	echo "Cannot find user $U"
	exit 1
fi
USER="`grep 'User login:' $TMP1 | awk ' { print $3 } '`"
rm $TMP1
if [ "$USER" != "$U" ]
then
	echo "Problem with user $U $USER"
	exit 1
fi

# We got the username, change the password.
# This was the old version, password expires.
#ipa passwd $U >/dev/null 2>&1 <<!EOF
#${3}
#${3}
#!EOF
# New version, direct kadmin, no expiry. Requires kadmind acl change.
kadmin -p ipaadmin/changepw@SWESTORE.SE -k \
  -t /home/ipaadmin/keys/ipaadmin-changepw.keytab -s 127.0.0.1 \
  -x ipa-setup-override-restrictions >/dev/null 2>&1 <<!EOF
cpw ${U}
${P}
${P}
!EOF
if [ $? -ne 0 ]
then
	echo "Error changing password for $U"
	exit 1
fi

# Finish.
exit 0

