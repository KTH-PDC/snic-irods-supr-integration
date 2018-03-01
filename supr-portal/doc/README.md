
# doc

This directory contains the developer documentation for the IPA
password change portal.

This file is in markdown format and there is an another one
in Wiki markup.

IPA is an identity mangement solution which can be used as a
central authentication server and it also includes a plethora of
other things as well (Kerberos, DNS, Certificates, Web admin
interface) which we don't really need or use.

It makes setting up and managing these rather complicated services
easier. It is supported by Red Hat.

We have got an IPA server installed to be used as an authentication
server for iRODS and possibly later for other services as
well. SUPR is our central database of users, projects and compute/storage
resource allocation.

The original goal is to enable users to set or change
their passwords on the IPA server whithout having IPA
credentials.

First the user gets redirected to a page in SUPR where he presents
his credentials. This can include SWAMID or also two factor authentication,
or just simply to log in using a userid and password. In case of a
successful authentication the user is issued with a one-time token or
kind of session cookie. That is used to identify him with SUPR and
it is also used to get the user information from SUPR. At the next
step the user is presented with a screen when he can type in the desired
password. Then an another CGI script gets invoked and that will check
the session cookie and eventually will call a script to change the
password for the user.

## More detailed description.

The IPA server among other things contains a Kerberos instance which
we use for authentication. It is configured during the IPA install
process. The standard Kerberos utilities work more or less the same
way but there are small changes done by the IPA people. There is an
admin web interface to make changes in user data and the Kerberos
settings. It is mostly for the server administrators but the users
themselves can also log in and access the system with limited
functionality. There is a way to extend this interface with plugins
but that did not work very well. The web server is an Apache web
server which will do the required actions mostly calling his own
API from the web server back end or executing Python scripts.

The web pages are done via Ajax / Dojo framework. Most of the web
pages are done in a way so all of them compiled into one big Javascript
blob (mangled, comments removed) and then pushed to the client browser.
The pages are dynamically created with this framework and so have a
uniform look and feel.

Looking from the other direction, when a user navigates to a page
there is a small amount of html code which is rendered by the browser,
which will then download the required Ajax and Dojo Javascript stuff.
The page is built and works in a semi-asynchronus fashion. Events can
trigger Ajax requests to be sent in a form of "RPC" call, kind of.
(WSGI plugins for the Apache web server.)

These are JSON formatted http post requests going to the web server
and can contain information gathered from the web page. These requests
are caught by the Ajax backend "RPC" server (which is like a daemon
process, written in Python), which will de-JSON them and turn them 
into Python data structures. This server process then contains the
Python code which will either call the API to carry out the request
or can call a script to do whatever is necessary. On completion it
will report back success or failure in similar "RPC" format.
(Test messages seem to have difficulties to get through.)

Our changes and additions are provided in the `files` directory
tree, with the pathname relative to the top of the file system
structure of the IPA server.

## Back-end

To start at the back-end those are the two files under
`/usr/lib/python2.7/site-packages/ipaserver`, `xmlserver.py` and
`rpcserver.py`. The first one needs just a one-liner to add
extra functionality. That the call to register the new class.
The second file is the RPC server itself. This requires a class
definition for the additional functionality. The code has parts
where it 'catches' the incoming request, parses the data in it
calls out to execute the portal script with the session cookie and
password arguments. The session cookie is coming from the client
browser, it was issued with it after the SUPR authentication. There
are also cookies at this point which contain other information
received from SUPR, most importantly the 'Center Person ID' which
in our case luckily the same as the IPA userid. The script which
eventually getting called is a python script. That script is
running as user `apache` so to be able to run Kerberos and IPA
commands runs a sudo command to run as user `ipaadmin` which has
the right to run the `ipa` and `kadmin` commands using Kerberos
keytabs. These are stashed under the 'ipaadmin' account.

For all these scripts there is a shell script `.sh` version which is
more like proof of concept and a Python script which is actually used.
We cannot use shell scripts for security reasons.

The script in question is `/usr/bin/supr-portal.py`, it's just an
envelope for `sudo`. The portal script calls
`/home/ipaadmin/supr/supr-portal.py`. That loads the cookies from
the previous browser page which are the session cookie and
information from SUPR about the user. It then calls the actual
password change script, `/home/ipaadmin/bin/ipa-passwd.py`.
That is driving `kadmin` to change the password for the specified
user, using a keytab to run as a special user with password
changing privileges. (That needs to be set up in the `kadmind` ACL
file, `/var/kerberos/krb5kdc/kadm5.acl`).

## Front-end from the user web browser perspective

The user navigates to the web address
`http://auth1.swestore.se/ipa/supr/supr-auth1.cgi`. This is file
`/usr/share/ipa/supr/supr-auth1.cgi` on the server. This in turn
will run script `/home/ipaadmin/supr/supr-auth1.py` on the server.
That is the first part of SUPR authentication. It uses
credentials stashed in a file to authenticate with SUPR
as a SUPR API user so it can call the API.
It calls the 'Initiate SUPR authentication` API function.
That, if succeeded returns a token (session cookie) and a URL which
is to be visited in the next step, as it issues a redirect.
Authentication will happen at a web page on the SUPR web site so
the SUPR credentials are never presented at a center web site.

At this point the user's browser will come back to the redirection
URL (`https://auth1.swestore.se/ipa/supr/supr-auth2.cgi`, which will
run `supr-auth2.py` from the same place) and in the second part of
the authentication process will issue a `Check Center Authentication`
request with the token. If this was successful SUPR data about the
user will be returned. The session cookie token and the SUPR
information will be packaged into cookies, sent down to the browser and
saved in a file on the server. Then as the last step an another
redirect happens to `https://auth1.swestore.se/ipa/ui/portal.html`.

This will load the password change page and we already have the
session cookie and the SUPR info cookies. The corresponding `portal.js`
script will be called and that will build the request to ask the
server for the password change. The session cookie in the browser will be
compared with the session cookie saved on the server and if that is
fine the password change will be carried out as described in the
previous section.


