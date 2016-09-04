# -*- coding: utf-8 -*-

""" Handler - Room
"""

from __future__ import absolute_import, print_function, unicode_literals

from .base import BaseHandler


class RoomHandler(BaseHandler):
    def initialize(self):
        """ This method run at handler object initialize.
        """
        super(self.__class__, self).initialize()
        self._RM = self._db['RoomMember']

    def get(self):
        self.render('room.html')

    def post(self):
        user = self.get_argument('user')
        room = self.get_argument('room')
        self._RM.update({'user': user},{'$set': {'user': user, 'room': room}}, upsert=True)
        self.set_cookie('user', user)
        self.redirect('/game')
