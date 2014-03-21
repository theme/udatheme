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

DEFAULT_BLOG_NAME= 'default_blog'

def jinja_temp(fn):
    print  '[path!]',  os.path.join( os.path.dirname(__file__))
    return JINJA_ENVIRONMENT.get_template(fn)

def blog_key(blog_name=DEFAULT_BLOG_NAME):
    """root entity: blog"""
    return ndb.Key('Blog', blog_name)

class Post(ndb.Model):
    """modle post"""
    title = ndb.StringProperty()
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)

class BlogPage(webapp2.RequestHandler):
    def get(self):
        posts_qry = Post.query(
                ancestor=blog_key()).order(-Post.date)
        posts= posts_qry.fetch(5)

        self.response.write(
                jinja_temp('index.jinja2').render({'posts':posts}))

class NewpostPage(webapp2.RequestHandler):
    def write_response(self,title='',content='',err=''):
        self.response.write( jinja_temp('newpost.jinja2').render({
            'subject':title,
            'content':content,
            'error':err}))
    def get(self):
        self.write_response()

    def post(self):
        p = Post(parent=blog_key())
        p.title = self.request.get("subject")
        p.content= self.request.get("content")

        if p.title and p.content :
            p.put()
            self.redirect("/blog")
        else:
            self.write_response(p.title,p.content,'need title & content')

class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.write("<h1>welcome</h1>")

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/blog', BlogPage),
    ('/blog/newpost', NewpostPage),
    ], debug=True)

