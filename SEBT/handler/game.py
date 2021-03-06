# -*- coding: utf-8 -*-

""" Handler - Game
"""

from __future__ import absolute_import, print_function, unicode_literals

from tornado.websocket import WebSocketHandler
from tornado.ioloop import IOLoop
from tornado import gen
from datetime import datetime
from pymongo.collection import ReturnDocument

import pymongo
import json
import hashlib
import time

from .base import BaseHandler
from ..db import db_gen
from ..poker import Poker, sebigtwo


ROUND_SEC = 30
DEADLINE_BUFFER_SEC = 2
CARD_INIT = 5
CARD_LIMIT = 13
ROOM_PLAYER_LIMIT = 7

class GameSocketHandler(WebSocketHandler):
    def prepare(self):
        self._db = db_gen()
        self._is_your_turn = False
        self._conn = False
        self._room = None
        self._M = None
        self._RM = self._db['RoomMember']
        self._RS = self._db['RoomStatus']
        self._hash = {}
        self._next_one_lock = False
        # self._db_catch = {}

    # ----- DB and DB catch-----
    def get_status(self):
        return self._RS.find_one({'_id': self._room}) if self._room else None

    def update_status(self, up, rtn=False, rtn_after=False):
        if not self._room:
            return None
        if not rtn:
            self._RS.update({'_id': self._room}, up)
            return None
        opt = ReturnDocument.AFTER if rtn_after else ReturnDocument.BEFORE
        return self._RS.find_one_and_update({'_id': self._room}, up, return_document=opt)

    def get_you(self, other=None):
        if not self._M:
            return None
        if other:
            return self._M.find_one({'name': other})
        user = self.get_cookie('user')
        return self._M.find_one({'name': user})

    def update_you(self, up, rtn=False, rtn_after=False, other=None):
        if not self._M:
            return None
        if not other:
            user = self.get_cookie('user')
        else:
            user = other
        if not rtn:
            self._M.update({'name': user}, up)
            return None
        opt = ReturnDocument.AFTER if rtn_after else ReturnDocument.BEFORE
        return self._M.find_one_and_update({'name': user}, up, return_document=opt)

    # ----- Game control -----
    def reset_game(self):
        print('Reset Game')
        self.update_status({'$set': {
                'status': 'init',
                'turn': '',
                'turn_num': -1,
                'setcard_num': -1,
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
        playing_user = self._M.find({'status':'init'}).count()
        if playing_user <= 1:
            print('Only 1 player QAQ.')
            return
        for m in self._M.find({'status':'init'}).sort('sign'):
            card = poker.pick_many(CARD_INIT)
            self._M.update({'_id': m['_id']}, {'$set': {
                    'status':'playing',
                    'your_card': card,
                    'card': CARD_INIT,
                    'deadline': 0
                }})
        fc = poker.pick()
        fp = self._M.find({'status':'playing'}).sort('sign').limit(1).next()
        self.update_status({'$set': {
                'status': 'playing',
                'current_card': [fc],
                'card': poker.to_list(),
                'turn_num': 0,
                'setcard_num': -1,
                'turn': fp['name'],
                'used_card': [],
                'place_cnt': 0,
                'playing_user': playing_user
            }})
        self.add_deadline(fp['name'])

    def stop_game(self, is_error=False):
        print('Stop Game')
        # TODO: Record scoreboard
        status = self.get_status()
        self._M.delete_many({'conn': False})
        self._M.update_many({'status':'gameover'}, {'$set': {'status': 'init'}})
        up = {
            'status': 'init',
            'turn_num': -1,
            'turn': '',
            'current_card': [],
            'playing_user': 0
        }
        if not self.get_you(other=status['room_manager']):
            up['room_manager'] = ''
        self.update_status({'$set': up})

    def signin_game(self):
        print('Signin')
        num = self._M.find({'status':'init'}).count()
        if num < ROOM_PLAYER_LIMIT:
            self.update_you({'$set': {'status': 'init', 'sign': datetime.utcnow()}})

    def signout_game(self):
        self.update_you({'$set': {'status': 'watching'}})

    def change_room_manager(self, name):
        self.update_status({'$set': {'room_manager': name}})

    # ----- Game Action -----
    def pick_card(self, other=None):
        print('pick!', other)
        status = self.get_status()
        if len(status['current_card']) == 0:
            if other:
                you = self.get_you(other)
                self.throw_card(you['your_card'][:1], other=other)
            else:
                print('Do not pick card!')
                self._next_one_lock = False
            return

        up = {}
        poker = None
        if len(status['card']):
            poker = Poker(status['card'])
        elif len(status['used_card']):
            poker = Poker(status['used_card'])
            poker.wash()
            up['used_card'] = []
        else:
            print('Error: Card not enough.')
            self._next_one_lock = False
            return
        
        c = poker.pick()
        up['card'] = poker.to_list()
        self.update_status({'$set': up})

        you = self.update_you({'$addToSet': {'your_card': c}, '$inc': {'card': 1}}, True, True, other)
        if you['card'] >= CARD_LIMIT:
            self.game_over(True, other=other)
        self.next_one(other=other)

    def throw_card(self, th_c, other=None):
        you = self.get_you(other)
        for c in th_c:
            if not c in you['your_card']:
                self._next_one_lock = False
                return
        status = self.get_status()
        crnt_set = sebigtwo.CardSet.gen(status['current_card'])
        your_set = sebigtwo.CardSet.gen(th_c)
        if your_set and (not crnt_set or sebigtwo.CardSet.comp(crnt_set, your_set) == 1):
            self.update_status({'$set': {'current_card': th_c, 'setcard_num': status['turn_num']}})
            up = {}
            up['your_card'] = [c for c in you['your_card'] if not c in th_c]
            up['card'] = len(up['your_card'])
            self.update_you({'$set': up}, other=other)
            if up['card'] == 0:
                self.game_over(other=other)
            self.next_one(other=other)
        else:
            if crnt_set and your_set and sebigtwo.CardSet.comp(crnt_set, your_set) == 0:
                print('Throw: Smaller.')
            else:
                print('Throw: Not the same type.')
            self._next_one_lock = False

    def change_card(self, th_c):
        you = self.get_you()
        for c in th_c:
            if not c in you['your_card']:
                self._next_one_lock = False
                return
        status = self.get_status()
        your_set = sebigtwo.CardSet.gen(th_c + status['current_card'])
        if len(status['current_card']) and your_set:
            self.update_status({'$set': {
                    'current_card': th_c + status['current_card'],
                    'setcard_num': status['turn_num']}})
            up = {}
            up['your_card'] = [c for c in you['your_card'] if not c in th_c]
            up['card'] = len(up['your_card'])
            self.update_you({'$set': up})
            if up['card'] == 0:
                self.game_over()
            self.next_one()
        else:
            if len(status['current_card']):
                print('Error type.')
            else:
                print('No current card.')
            self._next_one_lock = False

    # ----- Game Process -----
    def add_deadline(self, name):
        deadline = self.get_now_time() + ROUND_SEC
        print('Add deadline to %s: %s' % (name, deadline))
        self.update_you({'$set': {'deadline': deadline}}, other=name)
        you = self.get_you(other=name)
        print('You: %s' % you['deadline'])
        def callback(self, name, deadline):
            print('Player: %s\' deadline: %d' % (name, deadline))
            print('Now: %d' % time.time())
            you = self.get_you(other=name)
            print('Two deadline: %s and %s'%(you['deadline'] if you else 0, deadline))
            if you and you['deadline'] == deadline:
                self.pick_card(other=name)
        
        IOLoop.current().add_timeout(deadline+DEADLINE_BUFFER_SEC, callback, self, name, deadline)

    def next_one(self, other=None):
        self.update_you({'$set': {'deadline': 0}}, other=other)
        signin_num = self._M.find({'status': {'$in': ['playing', 'gameover']}}).count()
        if signin_num == 0:
            self._next_one_lock = False
            return
        status = self.get_status()
        trn = status['turn_num']
        for i in range(signin_num):
            trn = trn+1 if trn+1 < signin_num else 0
            next_p = self._M.find({'status': {'$in': ['playing', 'gameover']}}).sort('sign').skip(trn).limit(1).next()
            if next_p['status'] == 'playing':
                up = {}
                if status['setcard_num'] == trn:
                    up['current_card'] = []
                up['turn'] = next_p['name']
                up['turn_num'] = trn
                self.update_status({'$set': up})
                self.add_deadline(next_p['name'])
                self._next_one_lock = False
                return
        print('Error No Next One')

    def game_over(self, loss=False, other=None):
        # user = self.get_cookie('user')
        up = {}
        up['playing_user'] = -1
        if not loss:
            up['place_cnt'] = 1
        status = self.update_status({'$inc': up}, True, True)
        up = {}
        up['place'] = -1 if loss else status['place_cnt']
        up['status'] = 'gameover'
        up['your_card'] = []
        up['card'] = 0
        you = self.update_you({'$set': up}, True, False, other)
        if len(you['your_card']):
            self.update_status({'$push': {'used_card': {'$each': you['your_card']}}})
        # End the game
        print('End the game.')
        print(status['playing_user'])
        if status['playing_user'] == 1:
            last_user = self._M.find_one({'status': 'playing'})
            self.game_over(other=last_user['name'])
        elif status['playing_user'] == 0:
            self.stop_game()

    # ----- Time Function -----
    def get_now_time(self):
        return IOLoop.current().time()

    def check_deadline(self):
        you = self.get_you()
        return you['deadline'] == 0 or you['deadline'] > self.get_now_time()

    # ----- websocket ------
    def check_cache(self, key, data):
        h = hashlib.sha256(json.dumps(data,sort_keys=True)).hexdigest()
        oh = self._hash.get(key)
        if h == oh:
            return True
        self._hash[key] = h
        return False

    def write_json(self, data):
        self.write_message(json.dumps(data))

    def write_json_with_cache(self, key, data):
        if not self.check_cache(key,data):
            self.write_json(data)

    def on_message(self, message):
        # TODO: use data.get() instead of data['']
        status = self.get_status()
        you = self.get_you()
        data = json.loads(message)
        req = data['req']
        print('Get: %s' % req)
        if req == 'start':
            if status['status'] == 'init' and status['room_manager'] == you['name']:
                self.start_game()
        elif req == 'reset':
            if status['status'] == 'gameover' and status['room_manager'] == you['name']:
                self.reset_game()
        elif req == 'signin':
            if status['status'] == 'init' and you['status'] == 'watching':
                self.signin_game()
                if status['room_manager'] == '':
                    self.change_room_manager(you['name'])
        elif req == 'signout':
            if status['status'] == 'init' and you['status'] == 'init':
                self.signout_game()
        elif req == 'pick' or req == 'throw' or req == 'change':
            if status['status'] == 'playing' and self._is_your_turn and not self._next_one_lock and self.check_deadline():
                self._next_one_lock = True
                if req == 'pick':
                    self.pick_card()
                elif req == 'throw':
                    self.throw_card(data['card'])
                elif req == 'change':
                    self.change_card(data['card'])
        elif req == 'synctime':
            local = data['time']
            delay = self.get_now_time() - local
            # print('synctime: %s' %delay)
            self.write_json({'$set': {'delay': delay}})

    def get_player_list(self, is_game_init):
        if is_game_init:
            cursor = self._M.find({'status': 'init', 'conn': True}).sort('sign')
        else:
            cursor = self._M.find({'status': {'$in': ['playing', 'gameover']}}).sort('sign')
        without_keys = ['_id', 'sign', 'your_card']
        return [dict((k,x[k]) for k in x if k not in without_keys) for x in cursor]

    @gen.coroutine
    def game_loop(self):
        user = self.get_cookie('user')
        while self._conn:
            status = self.get_status()
            you = self.get_you()

            if not status or not you:
                yield gen.sleep(0.5)
                continue

            self._is_your_turn = you['name'] == status['turn']

            player_list = self.get_player_list(status['status'] == 'init')
            if not self.check_cache('players', player_list):
                self.write_json({'$set': {'players': player_list}})

            if not self.check_cache('status', status):
                self.write_json({'$set': {
                        'current_card': status['current_card'],
                        'room_manager': status['room_manager'],
                        'online_user': status['online_user'],
                        'status': status['status'],
                        'turn_num': status['turn_num'],
                        'turn': status['turn']
                    }})

            you_data = dict((k, you[k]) for k in ['status','your_card', 'name', 'deadline'])
            if not self.check_cache('you', you_data):
                self.write_json({'$set':{
                        'your_name': you_data['name'],
                        'your_card': you_data['your_card'],
                        'your_status': you_data['status'],
                        'deadline': you_data['deadline']
                    }})

            yield gen.sleep(0.5)

    @gen.coroutine
    def open(self):
        print("WebSocket opened")
        self._conn = True
        user = self.get_cookie('user')
        rm = self._RM.find_one({'user': user})
        if rm:
            self._room = rm['room']
            self._M = self._db[self._room+'-Member']
            self.update_status({'$addToSet': {'online_user': user}})
            self._M.update({'name': user},{
                    '$setOnInsert': {
                        'status': 'watching',
                        'name': user,
                        'card': 0,
                        'sign': 0,
                        'your_card': [],
                        'place': 0,
                        'deadline': 0,
                    },'$set':{
                        'conn': True
                    }},upsert=True)
            yield self.game_loop()
        else:
            # TODO: close connect
            print('Error!!!')

    def drop_room(self):
        print('drop room')
        self._RS.delete_one({'_id': self._room})
        self._RM.delete_many({'room': self._room})
        self._db.drop_collection(self._room+'-Member')

    def on_close(self):
        self._conn = False
        you = self.get_you()
        status = self.get_status()
        if you and status:
            if status['status'] == 'init' or you['status'] == 'watching':
                self._M.delete_one({'name': you['name']})
                if status['room_manager'] == you['name']:
                    new_rm = self._M.find_one({'status':'init'})
                    self.change_room_manager(new_rm['name'] if new_rm else '')
            else:
                self.update_you({'$set': {'conn': False}})
            status = self.update_status({'$pull': {'online_user': you['name']}}, True, True)
            if len(status.get('online_user', [])) == 0:
                self.drop_room()
            else:
                signin_num = self._M.find({'status': {'$in': ['playing', 'gameover']}, 'conn': True}).count()
                if signin_num == 0:
                    self.stop_game(True)
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
