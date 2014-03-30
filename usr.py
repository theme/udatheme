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

USERS_PARENT =  'users_parent'

# valid user info
import re

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile("^.{3,20}$")
EMAIL_RE = re.compile("^[\S]+@[\S]+\.[\S]+$")

def valid_username(username):
	return USER_RE.match(username)

def query_user( username ):
    key = ndb.Key( 'User', USERS_PARENT )
    qry = User.query(User.name == username, ancestor=key)
    try:
        usr = qry.fetch(1)[0]
        return usr
    except IndexError:
        return None

def unused_username(username):
    usr = query_user( username )
    if usr == None:
        return True
    else:
        return False

def valid_password(p):
	return PASS_RE.match(p)

def valid_email(email):
    if email:
        return EMAIL_RE.match(email)
    else:
        return True

# the user db
import hmac
import random
import hashlib
import string

class User( ndb.Model ):
    name = ndb.StringProperty()
    pass_hash  = ndb.StringProperty()
    salt = ndb.StringProperty()
    email = ndb.StringProperty()

def make_salt():
    return ''.join(random.choice(string.letters) for x in xrange(5))

def make_pw_hash(name, pw, salt):
    return "%s" % hashlib.sha256( name + pw + salt).hexdigest()

def user_parent_key():
    """root of user entities"""
    return ndb.Key( 'User', USERS_PARENT )

def sign_up_user(usr_username, usr_password, usr_email):
    u = User( parent = user_parent_key() )
    u.name = usr_username
    u.salt = make_salt()
    u.pass_hash = make_pw_hash( usr_username, usr_password, u.salt)
    u.email = usr_email

    return u.put()

# Handlers
USER_COOKIE_NAME='usr'

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

    def set_cookie_user(self, user_name, pass_hash ):
        self.response.headers.add_header('Set-Cookie',
                str( '%s=%s|%s; Path=/'
                %( USER_COOKIE_NAME, user_name, pass_hash) )
                )

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

        if not unused_username(usr_username):
            error_username = "usr exist"

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
            user_key = sign_up_user( usr_username, usr_password, usr_email)
            self.set_cookie_user( usr_username, user_key.get().pass_hash )
            self.redirect("/welcome")

    def get(self):
        self.write_form()

class WelcomeHandler(webapp2.RequestHandler):
    def get(self):
        usr_cookie = self.request.cookies[USER_COOKIE_NAME]
        usr_username = usr_cookie.split('|')[0]
        if not usr_username == '':
            self.response.out.write("Welcome! %s" % usr_username)
        else:
            self.redirect("/signup")

app = webapp2.WSGIApplication([	('/signup', SignUp),
                                ('/welcome', WelcomeHandler),],
                                debug=True)
