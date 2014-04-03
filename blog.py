import os
import cgi
import urllib2
import json
import time

from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.ext import ndb

import jinja2
import webapp2
from webapp2_extras import routes

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

def get_posts( most_recent_num ):
    posts_qry = Post.query(
                ancestor=blog_key()).order(-Post.created)
    posts= posts_qry.fetch(most_recent_num)
    return posts
    
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

class BlogFront(webapp2.RequestHandler):
    @classmethod
    def update_cache(cls):
        posts = get_posts(MOST_RECENT_POSTS)
        query_time = time.time()
        memcache.set( 'posts', (posts,query_time) )
        return (posts, query_time)

    def get(self):
        c = memcache.get( 'posts' )

        if c is None:
            posts, query_time = self.update_cache()
        else:
            posts, query_time = c

        front = jinja_temp('blog.jinja2').render({'posts':posts,
            'after_query_seconds': time.time()-query_time})
        self.response.write( front )

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
            post_id = p.put().id() 
            self.redirect( "/blog/%s" % str( post_id ) )
            BlogFront.update_cache()
            PermPost.update_cache(post_id)
        else:
            self.write_response( p.title, p.content, 'need title & content')

class PermPost(webapp2.RequestHandler):
    @classmethod
    def update_cache(cls, post_id):
        query_time = time.time()
        p = Post.get_by_id( int(post_id), parent = blog_key())
        memcache.set(post_id, (p, query_time))
        return (p,query_time)

    def get(self, **kwargs ):
        post_id = kwargs['post_id'] 

        # read cache
        c = memcache.get(post_id)
        if c is None:
            c = self.update_cache( post_id )

        p, query_time = c

        self.response.write( jinja_temp('permpost.jinja2').render({ 'post':p , 'queried_time_seconds': time.time() - query_time}))

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
    webapp2.SimpleRoute(r'/blog/?', handler=BlogFront, name='blogfront'),
    webapp2.SimpleRoute(r'/blog/?\.json', handler = JsonBlog, name='jsonblog'),
    routes.PathPrefixRoute(r'/blog', [
        webapp2.Route(r'/newpost', handler = NewpostPage, name='newpost'),
        webapp2.Route(r'/<post_id:\d+>', handler = PermPost, name='permpost'),
        webapp2.Route(r'/<post_id:\d+><:\.json$>', handler = JsonPost, name='jsonpost'),   
        ])],
    debug=True)

