import os
import cgi
import urllib
import logging
import re

from google.appengine.api import users
from google.appengine.ext import ndb

# check register input
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


# the User Model for ndb
import hmac
import random
import hashlib
import string

USERS_PARENT =  'users_parent'

class User( ndb.Model ):
    name = ndb.StringProperty()
    pass_hash  = ndb.StringProperty()
    salt = ndb.StringProperty()
    email = ndb.StringProperty()

def query_user( username ):
    key = ndb.Key( 'User', USERS_PARENT )
    qry = User.query( User.name == username, ancestor=key)
    try:
        usr = qry.fetch(1)[0]
        return usr
    except IndexError:
        return None

def check_user_exist( username ):
    return query_user( username ) or None

def is_unused_username( username ):
    return query_user( username ) == None


# secure hash utils
def make_salt():
    return ''.join(random.choice(string.letters) for x in xrange(5))

def make_pw_hash(name, pw, salt):
    return "%s" % hashlib.sha256( name + pw + salt).hexdigest()

def user_parent_key():
    """root of user entities"""
    return ndb.Key( 'User', USERS_PARENT )


# signup and check
def sign_up_user(usr_username, usr_password, usr_email):
    u = User( parent = user_parent_key() )
    u.name = usr_username
    u.salt = make_salt()
    u.pass_hash = make_pw_hash( usr_username, usr_password, u.salt)
    u.email = usr_email

    return u.put()

def check_user_hash( aun, ash ):
    '''args: user_name, salted_hash'''
    if aun == '' or ash == '':
        return False

    u = query_user( aun )
    if u and ash == u.pass_hash:
        return True
    else:
        return False

# signin check
def check_user_pass( aun, apass ):
    u = query_user( aun )
    if not u == None:
        new_hash = make_pw_hash( aun, apass, u.salt)
        if new_hash == u.pass_hash:
            return new_hash
        else:
            return 

