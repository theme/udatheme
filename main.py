import os
import cgi
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
        extensions=['jinja2.ext.autoescape'],
        autoescape=True)

DEFAULT_BLOG_NAME= 'default_blog'

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

        template = JINJA_ENVIRONMENT.get_template('temp/index.jinja2')
        self.response.write(template.render({'posts':posts}))

class NewpostPage(webapp2.RequestHandler):
    def get(self):
        self.redirect("/blog")

    def post(self):
        p = Post(parent=blog_key())
        p.title = self.request.get("title")
        p.content= self.request.get("content")
        p.put()
        self.redirect("/blog")

class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.write("<h1>welcome</h1>")

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/blog', BlogPage),
    ('/newpost', NewpostPage),
    ], debug=True)

