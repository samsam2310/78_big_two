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
        if not user:
            return self.render('room.html')
        self._RM.update({'user': user},{'$set': {'user': user, 'room': room}}, upsert=True)
        self.set_cookie('user', user)
        self._db['RoomStatus'].update({'_id': room},{
                '$setOnInsert':{
                    '_id': room,
                    'online_user': [],
                    'status': 'init',
                    'turn': '',
                    'current_card': [],
                    'card': [],
                    'used_card': [],
                    'room_manager': user
                }
            }, upsert=True)
        self.redirect('/game')
