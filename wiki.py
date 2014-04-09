import os
import cgi
import urllib
import logging

#from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2
from webapp2_extras import routes

# module
import usr

JINJA_ENVIRONMENT = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.join( os.path.dirname(__file__), 'templates')),
        extensions=['jinja2.ext.autoescape'],
        autoescape=True)

def jinja_temp(fn):
    return JINJA_ENVIRONMENT.get_template(fn)

# Handlers
USER_COOKIE_NAME='usr'

class UsrPageHandler(webapp2.RequestHandler):
    ''' read and write page with usr account form'''
    usr_cookie = '' # 'usr' cookie string
    coo_usr_name = ''
    coo_usr_hash = ''

    class current_usr:
        name = ''
        shash = ''
        pass

    def write_form(self, temp_name, arg={}):
        arg_usr = {
                "coo_usr_name": self.coo_usr_name,
                "usr":self.current_usr
                }
        self.response.out.write( jinja_temp(temp_name).render(arg) )

    def set_usr_cookie(self, uname, uhash):
        self.response.headers.add_header('Set-Cookie',
                str( '%s=%s|%s; Path=/' %(
                    USER_COOKIE_NAME, uname, uhash)))
                
    def rm_usr_cookie(self):
        self.response.headers.add_header('Set-Cookie',
                str( '%s=; Path=/; Expires=Thu, 01-Jan-1970 00:00:00 GMT' %(USER_COOKIE_NAME)))

    def get_usr_cookie(self):
        name = ''
        phash = ''
        try:
            self.usr_cookie = self.request.cookies[USER_COOKIE_NAME]
            name = self.usr_cookie.split('|')[0]
            phash = self.usr_cookie.split('|')[1]
        except:
            pass
        return ( name, phash )

    def get_current_user(self):
        name, phash = self.get_usr_cookie()
        if usr.check_user_hash( name, phash ):
            self.current_usr.name = name
            self.current_usr.shash = phash
            return self.current_usr
        else:
            return None

class SignUpHandler(UsrPageHandler):
    usr_name = ''
    err_name = ''
    usr_pw = '' # password
    err_pw = ''
    usr_pwv = '' # password verify
    err_pwv = ''
    usr_email = ''
    err_email = ''

    def signup_args(self):
        return {
            "username": self.usr_name,
            "error_username": self.err_name,
            "password": self.usr_pw,
            "passverify": self.usr_pwv,
            "error_password": self.err_pw,
            "error_passverify": self.err_pwv,
            "email": self.usr_email,
            "error_email": self.err_email
            }

    def get_signup_input(self):
        self.usr_name = self.request.get("username")
        self.usr_pw = self.request.get("password")
        self.usr_pwv= self.request.get("verify")
        self.usr_email = self.request.get("email")

    def post(self):
        self.get_signup_input()

        if not usr.valid_username(self.usr_name):
            self.err_name = "invalid user name"

        if not usr.is_unused_username(self.usr_name):
            self.err_name = "usr exist"

        if not self.usr_pw == self.usr_pwv:
            self.err_pwv = "not correspand"
            self.usr_pw = ""
            self.usr_pwv = ""

        elif not usr.valid_password(self.usr_pw):
            self.err_pw = "invalid password"
            self.usr_pw = ""
            self.usr_pwv = ""

        if not usr.valid_email(self.usr_email):
            self.err_email = "invalid email"

        if not ( self.err_name + self.err_pw + self.err_pwv
                + self.err_email == "" ):
            self.write_form('signup.jinja2', self.signup_args())
            logging.info( 'signup error' )
        else:
            user_key = usr.sign_up_user( self.usr_name,
                    self.usr_pw, self.usr_email)
            self.set_usr_cookie( self.usr_name,
                    user_key.get().pass_hash)
            # to current page
            logging.info( 'signup ok, redirect' )
            a = self.request.get('a')
            if a:
                self.redirect("%s" % a)
            else:
                self.redirect("/wiki")

    def get(self):
        self.write_form('signup.jinja2', self.signup_args())

class LoginHandler(UsrPageHandler):
    usr_name = ''
    err_name = ''
    usr_pw = '' # password
    err_pw = ''

    def login_args(self):
        return {
            "username": self.usr_name,
            "error_username": self.err_name,
            "password": self.usr_pw,
            "error_password": self.err_pw,
            }

    def get_login_input(self):
        self.usr_name = self.request.get("username")
        self.usr_pw = self.request.get("password")

    def post(self):
        self.get_login_input()

        # check user name
        if not usr.check_user_exist( self.usr_name ):
            self.err_name = 'no such user'
            self.write_form('login.jinja2', self.login_args())
            return

        # check user pass
        new_hash = usr.check_user_pass( self.usr_name, self.usr_pw)
        if new_hash:
            self.set_usr_cookie( self.usr_name, new_hash)
            # get current article from url
            a = self.request.get('a')
            self.redirect("%s" % a)

        else:
            self.err_pwv = 'wrong password'
            self.write_form('login.jinja2', login_args())

    def get(self):
        self.write_form('login.jinja2')

class LogoutHandler(UsrPageHandler):
    def get(self):
        self.rm_usr_cookie()
        a = self.request.get('a')
        if a :
            self.redirect("%s" % a)
        else:
            self.redirect("/wiki" )

# Wiki Article
DEFAULT_WIKI_NAME = 'default_wiki'

class Article(ndb.Model):
    title = ndb.StringProperty()
    content = ndb.StringProperty( indexed=False )
    created = ndb.DateTimeProperty(auto_now_add=True)

    def log(self):
        logging.info('%s, %s' % ( self.title, self.content ) )

def wiki_key( wiki_name = DEFAULT_WIKI_NAME ):
    return ndb.Key('Wiki', wiki_name)

def get_history( title = '' ):
    logging.info( ' get_history( %s)' % title )
    qry = Article.query( Article.title == title, ancestor=wiki_key()).order(Article.created)
    return  qry.fetch()

def get_article( title = '' , version = 0):
    logging.info( ' get_article( %s, %s)' % (title, str(version) ))
    try:
        articles = get_history( title )
        n = len( articles )
        if n > 0:
            if 0 == version: # latest
                return articles[ n - 1 ]
            if 1 <= version and version <= n:
                return articles[ version -1 ]
        else:
            return None
    except:
        return None
 
class WikiPage(UsrPageHandler):
    article = Article()

    def get_version(self):
        v = self.request.get('v')
        if v.isdigit():
            v = int( v )
        else:
            v = 1

    def get(self, title):
        logging.info( 'WikiPage get() %s' % title )
        name, phash = self.get_usr_cookie()

        a = get_article( title )
        logging.info( 'WikiPage get() a=%s' % a)
        if a is None:
            if name != '':
                self.redirect( '/_edit%s' % title )
            else:
                self.redirect( '/login?a=%s' % title )
        else:
            self.write_form('wiki.jinja2', {'article': a, 'usrname': name})

class HistoryPage(WikiPage):
    def get(self, title):
        his= get_history( title )
        s = ''
        for i in his:
            s += '%s, %s, %s <br> ' % ( i.created, i.title, i.content )

        self.response.write('historys: <br> %s ' % s)

    def post(self, title):
        self.response.write('POST: %s history page' % title)

class EditPage(WikiPage):
    def get(self, title):
        logging.info( 'EditPage get() %s' % title )
        name, phash = self.get_usr_cookie()

        # is user signed in ?
        if not usr.check_user_hash( name, phash ):
            a = self.request.get('a')
            self.redirect("/signup?a=%s" % a)
            return

        # render article
        v = self.get_version()
        a = get_article( title , v)
        if a is None:
            a = Article()
            a.title = title
        a.log()

        self.write_form('wiki_edit.jinja2', {'article': a, 'usrname': name})

    def post(self, title):
        name, phash = self.get_usr_cookie()

        # is usr signed in?
        if not usr.check_user_hash( name, phash ):
            a = self.request.get('a')
            self.redirect("/signup?a=%s" % a)
            return

        # save article
        v = self.get_version()
        a = get_article( title ) #TODO, retun a,v, to save v in Article db, not needed ?

        # always save new record
        a = Article(parent=wiki_key())
        a.title = title
        a.content = self.request.get('content')
        
        if a.title and a.content :
            a.put() 
            self.redirect( '%s' % title)
        else:
            self.write_form('wiki_edit.jinja2',{'article': self.article})

PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'
app = webapp2.WSGIApplication([('/signup', SignUpHandler),
    ('/login', LoginHandler),
    ('/logout', LogoutHandler),
    ('/_edit' + PAGE_RE, EditPage),
    ('/_history' + PAGE_RE, HistoryPage),
    (PAGE_RE, WikiPage),
    ],
    debug=True)

