# -*- coding: utf-8 -*-

""" Handler - Game
"""

from __future__ import absolute_import, print_function, unicode_literals

from tornado.websocket import WebSocketHandler
from tornado import gen
from datetime import datetime

import json
import hashlib

from .base import BaseHandler
from ..db import db, get_list_without_key


class GameSocketHandler(WebSocketHandler):
    def prepare(self):
        self._turn = False
        self._conn = False
        self._R = None
        self._RM = db['RoomMember']
        self._hash = {}

    def check_cache(self, key, data):
        h = hashlib.sha256(json.dumps(data,sort_keys=True)).hexdigest()
        oh = self._hash.get(key)
        if h == oh:
            return True
        self._hash[key] = h
        return False

    def write_json(self, data):
        print("Write: ")
        print(data)
        self.write_message(json.dumps(data))

    def write_json_with_cache(self, key, data):
        if not self.check_cache(key,data):
            self.write_json(data)

    @gen.coroutine
    def open(self):
        print("WebSocket opened")
        self._conn = True
        user = self.get_cookie('user')
        rm = self._RM.find_one({'user': user})
        if rm:
            room = rm['room']
            rmc = self._RM.find({'room': room}).count()
            self._C = db[room+'-Card']
            self._M = db[room+'-Member']
            self._S = db[room+'-Status']
            self._M.update({'name':user},{
                    '$setOnInsert': {
                        'name': user,
                        'conn': True,
                        'card': 0,
                        'sign': datetime.utcnow()
                    }},upsert=True)
            self.game_loop()
        else:
            print('Watching')

    def on_message(self, message):
        self.write_message(u"You said: " + message)

    @gen.coroutine
    def game_loop(self):
        while self._conn:
            players = get_list_without_key(self._M.find().sort('sign'), ['_id', 'sign'])
            if not self.check_cache('players', players):
                self.write_json({'$set': {'players': players}})
            yield gen.sleep(0.5)

    def on_close(self):
        self._conn = False
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
