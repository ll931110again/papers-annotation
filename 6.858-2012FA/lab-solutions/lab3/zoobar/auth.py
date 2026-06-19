from flask import g

from zoodb import *
import auth_client
import xfer_client

class User(object):
    def __init__(self):
        self.person = None
        self.token = None

    def checkLogin(self, username, password):
        token = auth_client.login(username, password)
        if token is not None:
            return self.loginCookie(username, token)
        return None

    def loginCookie(self, username, token):
        self.setPerson(username, token)
        return "%s#%s" % (username, token)

    def logout(self):
        self.person = None

    def addRegistration(self, username, password):
        token = auth_client.register(username, password)
        if token is None:
            return None
        xfer_client.check_in(username)
        return self.loginCookie(username, token)

    def checkCookie(self, cookie):
        if not cookie:
            return
        (username, token) = cookie.rsplit("#", 1)
        if auth_client.check_token(username, token):
            self.setPerson(username, token)

    def setPerson(self, username, token):
        persondb = person_setup()
        self.person = persondb.query(Person).get(username)
        self.token = token
        self.person.zoobars = xfer_client.balance(username)
