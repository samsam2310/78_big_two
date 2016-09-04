# -*- coding: utf-8 -*-

""" Handler - BaseHandler
"""

from __future__ import absolute_import, print_function, unicode_literals


from datetime import datetime

# import os
import tornado.web

from ..db import db


class BaseHandler(tornado.web.RequestHandler):
    def initialize(self):
        """ This method run at handler object initialize.
        """
        self._db = db

    def prepare(self):
        """This method is executed at the beginning of each request.
        """
        pass

    def on_finish(self):
        """Finish this response, ending the HTTP request 
        and properly close the database.
        """
        pass

    def write_error(self, error, **kwargs):
        pass
        # self.write({'error': error_str})

    @property
    def HTTPError(self):
        return tornado.web.HTTPError
