# -*- coding: utf-8 -*-

""" 78 big two - app
"""

from __future__ import absolute_import, print_function, unicode_literals


from .handler import route

import os

from tornado.ioloop import IOLoop
from tornado.web import Application
from tornado.httpserver import HTTPServer


def make_app():
    return Application(
        handlers = route,
        template_path = os.path.join(os.path.dirname(__file__), 'template'),
        static_path = os.path.join(os.path.dirname(__file__), 'static'),
        cookie_secret = os.environ.get('COOKIE_SECRET', ''),
        login_url = '/login',
        xsrf_cookies = False,
        debug = os.environ.get('DEBUG_MODE', '') == 'True',
        autoreload = False
        # default_handler_class = NotFoundHandler
    )


PORT = int(os.environ.get('LISTEN_PORT', 8000))

if __name__ == '__main__':
    make_app().listen(PORT, xheaders=True)
    print('Server start at port: %d' % PORT)
    IOLoop.current().start()
