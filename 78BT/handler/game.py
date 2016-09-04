# -*- coding: utf-8 -*-

""" Handler - Game
"""

from __future__ import absolute_import, print_function, unicode_literals

from tornado.websocket import WebSocketHandler

from .base import BaseHandler


class GameSocketHandler(WebSocketHandler):
    def open(self):
        print("WebSocket opened")

    def on_message(self, message):
        self.write_message(u"You said: " + message)

    def wait_for_your_turn(self):
        pass

    def on_close(self):
        print("WebSocket closed")


class GameHandler(BaseHandler):
    def initialize(self):
        """ This method run at handler object initialize.
        """
        super(self.__class__, self).initialize()
        self._RM = self._db['RoomMember']

    def get(self):
        user = self.get_cookie('user')
        rm = self._RM.find_one({'user': user})
        if not rm:
            raise self.HTTPError(403)
        room = rm['room']
        self.render('game.html', user=user, room=room)
