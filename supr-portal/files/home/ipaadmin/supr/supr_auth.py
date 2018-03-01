# -*- coding: utf-8 -*-

# Common definitions used by supr-auth1 and supr-auth2.

import random

# Random character string from /dev/random.
def get_nonce(chars = 8):
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    res = []
    sr = random.SystemRandom()
    for dummy_i in range(chars):
        res.append(sr.choice(alphabet))
    return "".join(res)


# Mix two character strings.
def mix_nonce (a, b):
    res = []
    if len(a) != len(b):
        msghtml("Error", "String length mismatch in mix_nonce")
        sys.exit(1)
    for i in range(len(a)):
        c1 = a[i]
        c2 = b[i]
        res.append(c1)
        res.append(c2)
    return "".join(res)

# Session cookie.
def get_session_cookie(token):
    a = token
    b = get_nonce(len(token))
    ab = mix_nonce(a, b)
    return ab


# Show message in html.
def msghtml(title, message):
    print "Content-type: text/html"
    print ""
    print "<html>"
    print "<head>"
    print "<title>" + title + "</title>"
    print "</head>"
    print "<body>"
    print message
    print "</body>"
    print "</html>"


# Print message in the html header section.
def msghead(header):
    print "Content-type: text/html"
    print ""
    print "<html>"
    print "<head>"
    print header
    print "<title></title>"
    print "</head>"
    print "<body>"
    print "</body>"
    print "</html>"


