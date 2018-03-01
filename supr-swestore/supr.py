# -*- coding: utf-8 -*-
# Connection to SUPR via the SUPR API

import json

# Using requests instead of the built-in
# urllib or urllib2 is so much nicer.
# http://docs.python-requests.org/
# EPEL/Fedora package: python-requests

import requests

# Our own exceptions

class SUPRException(Exception):
    pass

class SUPRHTTPError(SUPRException):
    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text
    def __str__(self):
        return "SUPRHTTPError(%d)" % (self.status_code)

class SUPRBadJSON(SUPRException):
    pass

# We want a dict with a twist: the ability to access it using
# attribute notation (X.key) as an alternative to indexing notation
# (X["key"]).  The main caveat is that this does not work for keys that
# have the same name as a dict method/attribute. If we have a key
# named "keys" in the dict, X["keys"] will get that, while X.keys will
# get the keys dict method. When in doubt, use normal indexing.

class SUPRdict(dict):
    def __getattr__(self, name):
        return self[name]

def SUPR_object_hook(x):
    return SUPRdict(x)

SUPRDecoder = json.JSONDecoder(object_hook = SUPR_object_hook)

# Our main class used to connect to SUPR and do GET/POST requests.

class SUPR(object):
    def __init__(self, user, password, base_url):
        self.user = user
        self.password = password
        self.base_url = base_url

    def get(self, url, params=None):
        url = self.base_url + url
        r = requests.get(url,
                         auth = (self.user, self.password),
                         params = params)
        if r.status_code == 200:
            try:
                decoded_data = SUPRDecoder.decode(r.content)
            except Exception:
                raise SUPRBadJSON
            return decoded_data
        else:
            raise SUPRHTTPError(r.status_code, r.text)

    def post(self, url, data):
        url = self.base_url + url
        try:
            encoded_data = json.dumps(data)
        except Exception:
            raise SUPRBadJSON

        r = requests.post(url,
                         auth = (self.user, self.password),
                         data = encoded_data)
        if r.status_code == 200:
            try:
                decoded_data = SUPRDecoder.decode(r.content)
            except Exception:
                raise SUPRBadJSON
            return decoded_data
        else:
            raise SUPRHTTPError(r.status_code, r.text)
