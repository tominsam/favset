#!/usr/bin/env python
import os
import wsgiref.handlers
from google.appengine.ext import webapp

from google.appengine.dist import use_library
use_library('django', '1.2')


import auth, favset

if __name__ == '__main__':

    handlers = [
        ('/', favset.Index),
        ('/signout', auth.Signout),
        ('/signin', auth.Signin),    
        ('/auth', auth.TokenDance),
    ]

    application = webapp.WSGIApplication(handlers, debug=True)
    wsgiref.handlers.CGIHandler().run(application)
