import os
import cgi
import urllib2
import json

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
    created = ndb.DateTimeProperty(auto_now_add=True)
    
    def toJson(self):
        p = { "subject": self.title,
                "content": self.content,
                "created": self.created.strftime("%a %b %d %H:%M:%S %Y")
            }
        return json.dumps( p )

class BlogPage(webapp2.RequestHandler):
    def get(self):
        posts_qry = Post.query(
                ancestor=blog_key()).order(-Post.created)
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
        p = Post.get_by_id( int(kwargs['post_id'] ), parent = blog_key())
        self.response.write( jinja_temp('permpost.jinja2').render({ 'post':p }))

class JsonPost(webapp2.RequestHandler):
    def get(self, *arg, **kwargs ):
        p = Post.get_by_id( int(kwargs['post_id'] ), parent = blog_key())
        self.response.headers.add_header('Content-Type',
                str( 'application/json_charset=utf-8' ))
        self.response.write( p.toJson() )

class JsonBlog(webapp2.RequestHandler):
    def get(self, *arg, **kwargs):
        posts_qry = Post.query(
                ancestor=blog_key()).order(-Post.created)
        posts= posts_qry.fetch(MOST_RECENT_POSTS)

        li = [ p.toJson() for p in posts ]
        self.response.headers.add_header('Content-Type',
                str( 'application/json_charset=utf-8' ))
        self.response.write( json.dumps(li))

app = webapp2.WSGIApplication([
    webapp2.Route(r'/blog', handler = BlogPage, name='blog'),
    webapp2.Route(r'/blog<:\.json$>', handler = JsonBlog, name='jsonblog'),
    webapp2.Route(r'/blog/newpost', handler = NewpostPage, name='newpost'),
    webapp2.Route(r'/blog/<post_id:\d+>', handler = PermPost, name='permpost'),
    webapp2.Route(r'/blog/<post_id:\d+><:\.json$>', handler = JsonPost, name='jsonpost'),
    ], debug=True)

