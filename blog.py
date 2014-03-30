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
MOST_RECENT_POSTS= 10

def jinja_temp(fn):
    return JINJA_ENVIRONMENT.get_template(fn)

def blog_key(blog_name=DEFAULT_BLOG_NAME):
    """root entity: blog"""
    return ndb.Key('Blog', blog_name)

def post_key(post_id,blog_name=DEFAULT_BLOG_NAME):
    return ndb.Key('Blog', blog_name, 'Post', str(post_id))
    
class Post(ndb.Model):
    title = ndb.StringProperty()
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)

class BlogPage(webapp2.RequestHandler):
    def get(self):
        posts_qry = Post.query(
                ancestor=blog_key()).order(-Post.date)
        posts= posts_qry.fetch(MOST_RECENT_POSTS)

        self.response.write(
                jinja_temp('blog.jinja2').render({'posts':posts}))

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
            self.redirect( "/blog/%s" % str( p.put().id() ) )
        else:
            self.write_response( p.title, p.content, 'need title & content')

class PermPost(webapp2.RequestHandler):
    def get(self, **kwargs ):
        #p = post_key( int(kwargs["post_id"] ) ).get()
        p = Post.get_by_id( int(kwargs['post_id'] ), parent = blog_key())
        print p
        self.response.write( jinja_temp('permpost.jinja2').render({ 'post':p }))

class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.write("<h1>welcome</h1>")

app = webapp2.WSGIApplication([
    webapp2.Route(r'/', handler = MainPage, name='home'),
    webapp2.Route(r'/blog', handler = BlogPage, name='blog'),
    webapp2.Route(r'/blog/newpost', handler = NewpostPage, name='newpost'),
    webapp2.Route(r'/blog/<post_id:\d+>', handler = PermPost, name='permpost'),
    ], debug=True)
