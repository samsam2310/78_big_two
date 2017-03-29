# -*- coding: utf-8 -*-

""" game controller
"""

from __future__ import absolute_import, print_function, unicode_literals

from tornado.ioloop import IOLoop


TIMEOUT_DELAY_SEC = 2

class Controller():
	def __init__(self, module, your_uid):
		self.room = None
		self.you = None
		self.your_uid = your_uid
		self.players = []
		self._module = module
		self._cmd_dict = dict()
		self._add_default_command()

	def __enter__():
		pass

	def __exit__():
		pass

	def _add_default_command(self):
		pass

	def call(self, cmd, data):
		fun = self._cmd_dict.get(cmd)
		fun(data) if fun else None

	def add_command(self, cmd_obj):
		self._com_dict[cmd_obj.name] = cmd_obj

	def is_room_manager(self, *a, **kw):
		return self.room['room_manager'] == self.you['_id']

	def is_room_status(self, sts, *a, **kw):
		return self.room['status'] == sts

	def is_your_status(self, sts, *a, **kw):
		return self.you['status'] == sts

	def is_before_your_deadline(self, *a, **kw):
		pass

	def room_init(self):
		init = {
			'status': 'init',
			'turn_uid': '',
			'turn_idx': -1,
			'playing_user_uids': []
		}
		init.update(self._module.Default_RoomStatus)
		self.room.update({'$set': init})

	def start_game(self):
		playing_user_num = len(self.room['playing_user_uids'])
		if playing_user_num == 1:
			# Only one player.
			return
		playing_user_uids = list(self.room['playing_user_uids'])
		sys_roomstatus = {
			'status': 'playing',
			'turn_idx': -1,
			'turn_uid': '',
			'playing_user_uids': playing_user_uids,
		}
		sys_playerstatus = {
			'status': 'playing',
			'room_id': self.room['_id'],
			'deadline': 0
		}
		self._module.start_game(playing_user_uids, sys_roomstatus, sys_playerstatus, self)
		self.start_turn(0, self)

	def get_next_one_idx(self):
		pass

	def start_turn(self, player_idx):
		self.room.update({'$set': {
				'turn_idx': player_idx,
				'turn_uid': self.room['playing_user_uids'][player_idx]
			}})
		self._module.start_turn(player_idx, self)

	def stop_game(self):
		pass

	def signin_game(self):
		pass

	def signout_game(self):
		pass

	def change_room_manager(self):
		pass

	def set_deadline(self, uid, delay, callback, *a, **kw):
		dltime = self.get_ioloop_time() + delay
		player = next(x for x in self.players if x['uid'] == uid)
		player.update({'$set': {'deadline': dltime}})

		def handler(uid, dltime, callback, *a, **kw):
			player = next(x for x in self.players if x['uid'] == uid)
			if you['deadline'] == dltime:
				callback(*a, **kw)

		IOLoop.current().add_timeout(dltime+TIMEOUT_DELAY_SEC, handler, uid, dltime, callback, *a, **kw)

	def clear_deadline(self, uid):
		player = next(x for x in self.players if x['uid'] == uid)
		player.update({'$set': {'deadline': 0}})

	def game_over(self):
		pass

	def get_ioloop_time(self):
		pass
