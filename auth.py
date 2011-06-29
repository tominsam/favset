# based on http://github.com/straup/gae-flickrapp/tree/master
import logging
import os
import time
import cgi
import traceback

from google.appengine.ext.webapp import template

from FlickrApp import FlickrApp, FlickrAppNewUserException, FlickrAppAPIException, FlickrAppException
from config import config

TEMPLATE_BASE = os.path.join(os.path.dirname(__file__), "templates")

class FlickrBaseApp(FlickrApp) :
    def __init__ (self) :
        FlickrApp.__init__(self, config['flickr_apikey'], config['flickr_apisecret'])
        self.config = config
        self.min_perms = config['flickr_minperms']
        self.flickr_ttl = 120
    
    def render(self, name, params):
        path = os.path.join(TEMPLATE_BASE, name)
        self.response.out.write(template.render(path, params))

    def render_error(self, error, suberror):
        path = os.path.join(TEMPLATE_BASE, "error.html")
        self.response.out.write(template.render(path, locals()))
    
    def flickr(self, method, **args):
        combined = dict(
            auth_token = self.user.token,
            **args
        )
        if method[0:7] != "flickr.":
            method = "flickr.%s"%method
        ret = self.proxy_api_call(method, combined, ttl = self.flickr_ttl)
        if ret["stat"] != "ok":
            raise FlickrAppAPIException(ret["message"])
        return ret
        
    def handle_exception(self, exception, debug_mode):
        error = u"%s: %s"%( exception.__class__.__name__, exception)
        stack = traceback.format_exc()

        logging.error(exception)
        logging.error(stack)

        path = os.path.join(TEMPLATE_BASE, "error.html")
        self.response.out.write(template.render(path, locals()))




# In Flickr-speak this is the "callback" URL that the user
# is redirected to once they have authed your application.

class TokenDance (FlickrBaseApp) :

    def get (self):
        try :
            new_users = True
            self.do_token_dance(allow_new_users=new_users)
            
        except FlickrAppNewUserException, e:
            return self.render_error('New user signups are currently disabled.')

        except FlickrAppAPIException, e:
            return self.render_error('The Flickr API is being cranky.')

        except FlickrAppException, e:
            return self.render_error('Application error: %s' % e)
      
        except Exception, e:
            return self.render_error('Unknown error: %s' % e)

# This is where you send a user to sign in. If they are not
# already authed then the application will take care generating
# Flickr Auth frobs and other details.

class Signin (FlickrBaseApp) :
    
    def get (self) :
        if self.check_logged_in(self.min_perms) :
            self.redirect("/")
            
        self.do_flickr_auth(self.min_perms, '/')

# This is where you send a user to log them out of your
# application. The user may or may not still be logged in to
# Flickr. Note how we're explictly zero-ing out the cookies;
# that should probably be wrapped up in a helper method...

class Signout (FlickrBaseApp) :

    def post (self) :
        if not self.check_logged_in(self.min_perms) :
            self.redirect("/")

        crumb = self.request.get('crumb')

        if not crumb :
            self.redirect("/")
            
        if not self.validate_crumb(self.user, "logout", crumb) :
            self.redirect("/")

        self.response.headers.add_header('Set-Cookie', 'ffo=')
        self.response.headers.add_header('Set-Cookie', 'fft=')    
        
        self.redirect("/")
    
