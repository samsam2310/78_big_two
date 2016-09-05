# -*- coding: utf-8 -*-

""" Handler - Game
"""

from __future__ import absolute_import, print_function, unicode_literals

from tornado.websocket import WebSocketHandler
from tornado import gen
from datetime import datetime
from pymongo.collection import ReturnDocument

import pymongo
import json
import hashlib

from .base import BaseHandler
from ..db import db, get_list_without_key
from ..poker import Poker


class GameSocketHandler(WebSocketHandler):
    def prepare(self):
        self._turn = False
        self._conn = False
        self._R = None
        self._RM = db['RoomMember']
        self._hash = {}
        self._status = None

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
            self._room = rm['room']
            self._M = db[self._room+'-Member']
            self._RS = db['RoomStatus']
            self._RS.update({'_id': self._room}, {'$addToSet': {'online_user': user}})
            self._M.update({'name': user},{
                    '$setOnInsert': {
                        'status': 'init',
                        'name': user,
                        'card': 0,
                        'sign': datetime.utcnow(),
                        'your_card': []
                    },'$set':{
                        'conn': True
                    }},upsert=True)
            self.game_loop()
        else:
            print('Watching')

    def start_game(self):
        print('Start Game')
        poker = Poker()
        poker.wash()
        for m in self._M.find().sort('sign'):
            card = poker.pick_many(5)
            self._M.update({'_id': m['_id']}, {'$set': {'status':'playing','your_card': card, 'card': 5}})
        fc = poker.pick()
        fp = self._M.find().sort('sign').limit(1).next()
        self._RS.update({'_id': self._room},{'$set': {
                'ststus': 'playing',
                'current_card': [fc],
                'card': poker.to_list(),
                'turn_num': 0,
                'turn': fp['name'],
                'used_card': []
            }})

    def on_message(self, message):
        user = self.get_cookie('user')
        data = json.loads(message)
        req = data['req']
        if req == 'start':
            if self._status and self._status['status'] == 'init' and self._status['room_manager'] == user:
                self.start_game()
        elif req == '':
            pass

    @gen.coroutine
    def game_loop(self):
        user = self.get_cookie('user')
        while self._conn:
            players = get_list_without_key(self._M.find().sort('sign'), ['_id', 'sign', 'your_card'])
            if players and not self.check_cache('players', players):
                self.write_json({'$set': {'players': players}})
            status = self._status = self._RS.find_one({'_id': self._room})
            if status and not self.check_cache('status', status):
                self.write_json({'$set': {
                        'current_card': status['current_card'],
                        'room_manager': status['room_manager'],
                        'online_user': status['online_user'],
                        'status': status['status']
                    }})
            tmp = self._M.find_one({'name': user})
            you = dict((k, tmp[k]) for k in ['your_card', 'name'])
            if you and not self.check_cache('you', you):
                self.write_json({'$set':{
                        'your_name': you['name'],
                        'your_card': you['your_card']
                    }})
            yield gen.sleep(0.5)

    def drop_room(self):
        self._RS.delete_one({'_id': self._room})
        db.drop_collection(self._room+'-Member')

    def on_close(self):
        user = self.get_cookie('user')
        self._M.update({'name':user},{'$set': {'conn': False}})
        self._conn = False
        rs = self._RS.find_one_and_update(
                {'_id': self._room},
                {'$pull': {'online_user': user}},
                return_document=ReturnDocument.AFTER)
        if not rs or len(rs['online_user']) == 0:
            self.drop_room()
        print("WebSocket closed")


class GameHandler(BaseHandler):
    def initialize(self):
        """ This method run at handler object initialize.
        """
        super(self.__class__, self).initialize()
        self._RM = self._db['RoomMember']
        self._RS = self._db['RoomStatus']

    def get(self):
        user = self.get_cookie('user')
        rm = self._RM.find_one({'user': user})
        if not rm:
            return self.redirect('/room')
        rs = self._RS.find_one({'_id': rm['room']})
        if not rs:
            return self.redirect('/room')
        self.render('game.html', user=user, room=rm['room'])
