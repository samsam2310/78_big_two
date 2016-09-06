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
from ..db import db_gen, get_list_without_key
from ..poker import Poker


CARD_LIMIT = 12

class GameSocketHandler(WebSocketHandler):
    def prepare(self):
        self._db = db_gen()
        self._is_your_turn = False
        self._conn = False
        self._R = None
        self._RM = self._db['RoomMember']
        self._RS = self._db['RoomStatus']
        self._hash = {}
        self._status = None
        self._next_one_lock = False

    def check_cache(self, key, data):
        h = hashlib.sha256(json.dumps(data,sort_keys=True)).hexdigest()
        oh = self._hash.get(key)
        if h == oh:
            return True
        self._hash[key] = h
        return False

    def write_json(self, data):
        # print("Write: ")
        # print(data)
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
            self._M = self._db[self._room+'-Member']
            self._RS.update({'_id': self._room}, {'$addToSet': {'online_user': user}})
            self._M.update({'name': user},{
                    '$setOnInsert': {
                        'status': 'init',
                        'name': user,
                        'card': 0,
                        'sign': datetime.utcnow(),
                        'your_card': [],
                        'place': 0,
                    },'$set':{
                        'conn': True
                    }},upsert=True)
            you = self._M.find_one({'name': user})
            yield self.game_loop()
        else:
            print('Watching')

    def check_game_status(self, sts):
        return self._status and self._status['status'] == sts

    def reset_game(self):
        print('Reset Game')
        self._RS.update({'_id': self._room},{'$set': {
                'status': 'init',
                'turn': '',
                'turn_num': -1,
                'current_card': [],
                'card': [],
                'used_card': [],
                'place_cnt': 0,
                'playing_user': 0,
            }})

    def start_game(self):
        print('Start Game')
        poker = Poker()
        poker.wash()
        rmc = 0
        for m in self._M.find().sort('sign'):
            card = poker.pick_many(5)
            self._M.update({'_id': m['_id']}, {'$set': {'status':'playing','your_card': card, 'card': 5}})
            rmc += 1
        fc = poker.pick()
        fp = self._M.find().sort('sign').limit(1).next()
        self._RS.update({'_id': self._room},{'$set': {
                'status': 'playing',
                'current_card': [fc],
                'card': poker.to_list(),
                'turn_num': 0,
                'turn': fp['name'],
                'used_card': [],
                'place_cnt': 0,
                'playing_user': rmc
            }})

    def pick_card(self):
        user = self.get_cookie('user')
        card = self._status['card']
        used_card = self._status['used_card']
        poker = Poker(card)
        c = poker.pick()
        if not c:
            poker = Poker(used_card)
            used_card = []
            poker.wash()
            c = poker.pick()
        card = poker.to_list()
        self._RS.update({'_id': self._room}, {'$set': {'card': card, 'used_card': used_card}})

        if c:
            you = self._M.find_one_and_update({'name': user},
                    {'$addToSet': {'your_card': c}, '$inc': {'card': 1}},
                    return_document=ReturnDocument.AFTER)
        if not c or you['card'] >= CARD_LIMIT:
            self.game_over(True)
        self.next_one()

    def throw_card(self, th_cs):
        you = self._M.find_one({'name': user})
        for c in th_cs:
            if not c in you['your_card']:
                self._next_one_lock = False
                return
        pass
        self.next_one()

    def next_one(self):
        rmc = self._M.find().count()
        ntn = self._status['turn_num']
        for i in range(rmc):
            ntn = ntn+1 if ntn+1<rmc else 0
            nxtp = self._M.find().sort('sign').skip(ntn).limit(1).next()
            print("DB: ntn: %d, nxtp: %s" % (ntn, nxtp['name']))
            if nxtp['status'] == 'playing':
                self._RS.update({'_id': self._room},{'$set': {'turn': nxtp['name'], 'turn_num': ntn}})
                self._next_one_lock = False
                break

    def game_over(self, loss=False):
        user = self.get_cookie('user')
        status = self._RS.find_one_and_update({'_id': self._room},
                {'$inc': {'playing_user': -1, 'place_cnt': 0 if loss else 1 }},
                return_document=ReturnDocument.AFTER)
        place = -1 if loss else status['place_cnt']
        you = self._M.find_one_and_update({'name': user}, {'$set': {
                'status': 'gameover',
                'place': place,
                'your_card': [],
                'card': 0}})
        self._RS.update({'_id': self._room}, {'$push': {'used_card': {'$each': you['your_card']}}})

    def stop_game(self):
        print('Stop Game')
        self._RS.update({'_id': self._room},{'$set': {
                'status': 'gameover',
                'turn_num': -1,
                'turn': '',
                'playing_user': 0
            }})

    def on_message(self, message):
        user = self.get_cookie('user')
        data = json.loads(message)
        req = data['req']
        if req == 'start':
            if self.check_game_status('init') and self._status['room_manager'] == user:
                self.start_game()
        elif req == 'pick':
            print("pick")
            if self.check_game_status('playing') and self._is_your_turn and not self._next_one_lock:
                self._next_one_lock = True
                self.pick_card()
        elif req == 'reset':
            if self.check_game_status('gameover') and self._status['room_manager'] == user:
                self.reset_game()
        elif req == 'throw':
            if self.check_game_status('playing') and self._is_your_turn and not self._next_one_lock:
                self._next_one_lock = True
                self.throw_card(data['card'])
        elif req == '':
            pass

    @gen.coroutine
    def game_loop(self):
        user = self.get_cookie('user')
        while self._conn:
            players = get_list_without_key(self._M.find().sort('sign'), ['_id', 'sign', 'your_card'])
            status = self._status = self._RS.find_one({'_id': self._room})
            you = self._M.find_one({'name': user})

            self._is_your_turn = status and you and you['name'] == status['turn']
            if not self._next_one_lock and status and you and status['playing_user'] == 1 and you['status'] == 'playing':
                self.game_over()
                self.stop_game()

            if players and not self.check_cache('players', players):
                self.write_json({'$set': {'players': players}})
            if status and not self.check_cache('status', status):
                self.write_json({'$set': {
                        'current_card': status['current_card'],
                        'room_manager': status['room_manager'],
                        'online_user': status['online_user'],
                        'status': status['status'],
                        'turn_num': status['turn_num'],
                        'turn': status['turn'],
                    }})
            you_data = dict((k, you[k]) for k in ['your_card', 'name'])
            if you_data and not self.check_cache('you', you_data):
                self.write_json({'$set':{
                        'your_name': you_data['name'],
                        'your_card': you_data['your_card']
                    }})

            yield gen.sleep(0.5)

    def drop_room(self):
        self._RS.delete_one({'_id': self._room})
        self._db.drop_collection(self._room+'-Member')

    def on_close(self):
        user = self.get_cookie('user')
        self._M.update({'name':user},{'$set': {'conn': False}})
        self._conn = False
        rs = self._RS.find_one_and_update(
                {'_id': self._room},
                {'$pull': {'online_user': user}},
                return_document=ReturnDocument.AFTER)
        if not rs or rs.get('online_user') and len(rs['online_user']) == 0:
            self.drop_room()
        print("WebSocket closed")


class GameHandler(BaseHandler):
    def prepare(self):
        """ This method run at handler object initialize.
        """
        super(self.__class__, self).prepare()
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
