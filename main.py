#!/usr/bin/env python
import os
import wsgiref.handlers
from google.appengine.ext import webapp

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
