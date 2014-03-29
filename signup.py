import os
import cgi
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.join( os.path.dirname(__file__), 'templates')),
        extensions=['jinja2.ext.autoescape'],
        autoescape=True)

def jinja_temp(fn):
    return JINJA_ENVIRONMENT.get_template(fn)

import re

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile("^.{3,20}$")
EMAIL_RE = re.compile("^[\S]+@[\S]+\.[\S]+$")

def valid_username(username):
	return USER_RE.match(username)

def valid_password(p):
	return PASS_RE.match(p)

def valid_email(email):
    if email:
        return EMAIL_RE.match(email)
    else:
        return True

class SignUp(webapp2.RequestHandler):
    def write_form(self,
            username="",
            error_username="",
            password="",
            passverify="",
            error_password="",
            error_passverify="",
            email="",
            error_email=""):

        self.response.out.write(
                jinja_temp('signup.jinja2').render({
            "username": username,
            "error_username": error_username,
            "password": password,
            "passverify": passverify,
            "error_password": error_password,
            "error_passverify": error_passverify,
            "email": email,
            "error_email": error_email}))

    def post(self):
        usr_username = self.request.get("username")
        usr_password = self.request.get("password")
        usr_passverify = self.request.get("verify")
        usr_email = self.request.get("email")

        error_username = ""
        error_password = ""
        error_passverify = ""
        error_email = ""

        if not valid_username(usr_username):
            error_username = "invalid user name"

        if not usr_password == usr_passverify :
            error_passverify = "not correspand"
            usr_password = ""
            usr_passverify = ""

        elif not valid_password(usr_password):
            error_password = "invalid password"
            usr_password = ""
            usr_passverify = ""

        if not valid_email(usr_email):
            error_email = "invalid email"

        if ( error_username + error_password + error_passverify + error_email != "" ):
            self.write_form(usr_username, error_username,
				"", "", error_password, error_passverify,
				usr_email, error_email)
        else:
            self.redirect("/welcome?name=%s" % usr_username)

    def get(self):
        self.write_form()

class WelcomeHandler(webapp2.RequestHandler):
    def get(self):
	usr_username = self.request.get("name")
        self.response.out.write("Welcome! %s" % usr_username)

app = webapp2.WSGIApplication([	('/signup', SignUp),
                                ('/welcome', WelcomeHandler),],
                                debug=True)
