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

class UsrPageHandler(webapp2.RequestHandler):
    ''' read and write page with usr account form'''
    usr_name = ''
    err_name = ''
    usr_pw = '' # password
    err_pw = ''
    usr_pwv = '' # password verify
    err_pwv = ''
    usr_email = ''
    err_email = ''

    usr_cookie = '' # 'usr' cookie string
    coo_usr_name = ''
    coo_usr_hash = ''

    def get_usr_input(self):
        self.usr_name = self.request.get("username")
        self.usr_pw = self.request.get("password")
        self.usr_pwv= self.request.get("verify")
        self.usr_email = self.request.get("email")
        self.err_name = ''
        self.err_pw = ''
        self.err_pwv = ''
        self.err_email = ''

    def write_form(self, temp_name):
        self.response.out.write(
            jinja_temp(temp_name).render({
                "username": self.usr_name,
                "error_username": self.err_name,
                "password": self.usr_pw,
                "passverify": self.usr_pwv,
                "error_password": self.err_pw,
                "error_passverify": self.err_pwv,
                "email": self.usr_email,
                "error_email": self.err_email }))

    def set_cookie_user(self):
        self.response.headers.add_header('Set-Cookie',
                str( '%s=%s|%s; Path=/' %(
                    USER_COOKIE_NAME, self.coo_usr_name,
                    self.coo_usr_hash)))
                
    def rm_cookie_user(self):
        self.response.headers.add_header('Set-Cookie',
                str( '%s=; Path=/; Expires=Thu, 01-Jan-1970 00:00:00 GMT' %(USER_COOKIE_NAME)))

    def get_cookie_user(self):
        self.usr_cookie = self.request.cookies[USER_COOKIE_NAME]
        self.coo_usr_name = self.usr_cookie.split('|')[0]
        self.coo_usr_hash = self.usr_cookie.split('|')[1]

class SignUpHandler(UsrPageHandler):
    def post(self):
        self.get_usr_input()

        if not valid_username(self.usr_name):
            self.err_name = "invalid user name"

        if not unused_username(self.usr_name):
            self.err_name = "usr exist"

        if not self.usr_pw == self.usr_pwv:
            self.err_pwv = "not correspand"
            self.usr_pw = ""
            self.usr_pwv = ""

        elif not valid_password(self.usr_pw):
            self.err_pw = "invalid password"
            self.usr_pw = ""
            self.usr_pwv = ""

        if not valid_email(self.usr_email):
            self.err_email = "invalid email"

        if not ( self.err_name + self.err_pw + self.err_pwv +
                self.err_email == "" ):
            self.write_form('signup.jinja2')
        else:
            user_key = sign_up_user( self.usr_name, self.usr_pw,
                    self.usr_email)
            self.coo_usr_name = self.usr_name
            self.coo_usr_hash = user_key.get().pass_hash
            self.set_cookie_user()
            self.redirect("/blog/welcome")

    def get(self):
        self.write_form('signup.jinja2')

class LoginHandler(UsrPageHandler):
    def post(self):
        self.get_usr_input()

        usr = query_user(self.usr_name)
        if not usr == None:
            new_hash = make_pw_hash(self.usr_name, self.usr_pw, usr.salt)
            if new_hash == usr.pass_hash:
                self.coo_usr_name = self.usr_name
                self.coo_usr_hash = new_hash
                self.set_cookie_user()
                self.redirect("/blog/welcome")
            else:
                self.err_pwv = 'wrong password'
                self.write_form('login.jinja2')
        else:
            self.err_name = 'no such user'
            self.write_form('login.jinja2')

    def get(self):
        self.write_form('login.jinja2')

class WelcomeHandler(UsrPageHandler):
    def get(self):
        self.get_cookie_user()
        if not self.coo_usr_name == '':
            self.response.out.write("Welcome! %s" % self.coo_usr_name)
        else:
            self.redirect("/blog/login")

class LogoutHandler(UsrPageHandler):
    def get(self):
        self.rm_cookie_user()
        self.redirect("/blog/signup")
        
app = webapp2.WSGIApplication(
        [('/blog/signup', SignUpHandler),
            ('/blog/login', LoginHandler),
            ('/blog/logout', LogoutHandler),
            ('/blog/welcome', WelcomeHandler),],
        debug=True)
