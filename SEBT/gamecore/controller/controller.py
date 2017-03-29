# -*- coding: utf-8 -*-

""" game controller
"""

from __future__ import absolute_import, print_function, unicode_literals

from tornado.ioloop import IOLoop


TIMEOUT_DELAY_SEC = 2
RESET_GAME_SEC = 5

class Controller():
	def __init__(self, module, your_uid):
		self.room = None
		self.you = None
		self.your_uid = your_uid
		self.players = []
		self._module = module
		self._cmd_dict = dict()
		self._add_default_command()

	def _add_default_command(self):
		pass

	def connect():
		pass

	def disconnect():
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

	DEFAULT_ROOM_STATUS = {
		'status': 'init',
		'turn_uid': '',
		'turn_idx': -1,
		'player_uids': [],
		'rank_idx': 1
	}
	def room_init(self):
		init_status = DEFAULT_ROOM_STATUS.copy().update(self._module.Default_RoomStatus)
		self.room.update(init_status)

	def start_game(self):
		player_num = len(self.room['player_uids'])
		if player_num == 1:
			# Only one player.
			return
		player_uids = list(self.room['player_uids'])
		sys_roomstatus = {
			'status': 'playing',
			'player_uids': player_uids,
		}
		sys_playerstatus = {
			'status': 'playing',
			'room_id': self.room['_id'],
			'deadline': 0,
			'conn': False,
		}
		self._module.start_game(player_uids, sys_roomstatus, sys_playerstatus, self)
		self.start_turn_by_player_idx(0, self)

	def get_player_by_uid(self, uid):
		return next((x for x in self.players if x['uid'] == uid), None)

	def get_player_idx_by_uid(self, uid):
		return next((idx for idx,x in enumerate(self.players) if x['uid'] == uid), -1)

	def get_playing_num(self):
		return sum(x['status']=='playing' for x in self.players)

	def next_player_turn_by_uid(self, uid):
		idx = get_player_idx_by_uid(uid)
		players = self.players
		plen = len(players)
		nx_idx = next( i % plen
						for i in range(idx+1, idx+plen)
						if players[i%plen]['status'] == 'playing', -1)
		if nx_idx == -1:
			# Game is done, stop game.
			return self.stop_game()
		playing_num = self.get_playing_num()
		if playing_num == 1:
			return self._module.last_one_player_by_idx(idx, self)
		self.start_turn_by_player_idx(nx_idx)

	def start_turn_by_player_idx(self, player_idx):
		self.room.update({
				'turn_idx': player_idx,
				'turn_uid': self.room['player_uids'][player_idx]
			})
		self._module.start_turn_by_player_idx(player_idx, self)

	def stop_game(self):
		# TODO: Record scoreboard
		self.room.update({
				'status': 'gameover',
				'turn_idx': -1,
				'turn_uid': '',
				'card_on_table': []
			})
		reset_time = self.get_ioloop_time() + RESET_GAME_SEC
		IOLoop.current().add_timeout(reset_time, self.reset_game)

	def reset_game(self):
		player_uids = [x['uid'] for x in self.players if x['conn']]
		for x in self.players:
			x.close()
		self.players = []
		self.you = None
		room_status = DEFAULT_ROOM_STATUS.copy()
		room_status.update({'player_uids': player_uids})
		self.room.update(room_status)

	def signin_game(self):
		pass

	def signout_game(self):
		pass

	def change_room_manager(self):
		pass

	def set_deadline(self, uid, delay, callback, *a, **kw):
		dltime = self.get_ioloop_time() + delay
		player = next(x for x in self.players if x['uid'] == uid)
		player.update({'deadline': dltime})

		def handler(uid, dltime, callback, *a, **kw):
			player = next(x for x in self.players if x['uid'] == uid)
			if you['deadline'] == dltime:
				callback(*a, **kw)

		IOLoop.current().add_timeout(dltime+TIMEOUT_DELAY_SEC, handler, uid, dltime, callback, *a, **kw)

	def clear_deadline(self, uid):
		player = self.get_player_by_uid(uid)
		player.update({'deadline': 0})

	RANK_LOSS = 1
	RANK_FRONT = 2
	RANK_BACK = 3 # Cannot be use with RANK_LOSS
	def gameover_by_uid(self, uid, rank_opt=RANK_FRONT):
		player = self.get_player_by_uid(uid)
		new_rank_idx = self.room['rank_idx']
		if rank_opt == self.RANK_FRONT:
			rank = new_rank_idx
			new_rank_idx += 1
		elif rank_opt == self.RANK_BACK:
			playing_num = self.get_playing_num()
			rank = playing_num + new_rank_idx - 1
		elif rank_opt == self.RANK_LOSS:
			rank = -1
		else:
			# Error
			rank = -1
		sys_roomstatus = {
			'rank_idx': new_rank_idx
		}
		sys_playerstatus = {
			'status': 'gameover',
			'rank': rank
		}
		self._module.gameover_by_uid(uid, sys_roomstatus, sys_roomstatus, self)

	def get_ioloop_time(self):
		return IOLoop.current().time()
