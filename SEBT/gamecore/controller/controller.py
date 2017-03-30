# -*- coding: utf-8 -*-

""" game controller
"""

from __future__ import absolute_import, print_function, unicode_literals

from tornado.ioloop import IOLoop

import functools

from ...db import RealTimeCollection, ColRoom, ColPlayer


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
		self._load_command()

	def __del__(self):
		self.room.close()
		for player in self.players:
			player.close()

	def _load_command(self):
		cmd = Command('signin', self.signin_game)
		cmd.add_permission_checker(functools.partial(self.is_room_status, sts='init'))
		self._cmd_dict['signin'] = cmd

		cmd = Command('signout', self.signout_game)
		cmd.add_permission_checker(functools.partial(self.is_room_status, sts='init'))
		self._cmd_dict['signout'] = cmd

		cmd = Command('start', self.start_game)
		cmd.add_permission_checker(functools.partial(self.is_room_status, sts='init'))
		cmd.add_permission_checker(self.is_room_manager)
		self._cmd_dict['start'] = cmd

		for cmd in self._module.Command_list:
			self._cmd_dict[cmd.name] = cmd

	def handle_room_status(self, data):
		if self.room['status'] == 'playing' and not self.players:
			# Connect to Player list
			cursor = ColPlayer.find({'room_id': self.room['_id']}).sort('player_idx')
			for player_status in cursor:
				player = RealTimeCollection(ColPlayer.name, player_status)
				self.players.append(player)
				if self.your_uid == player['uid']:
					self.you = player
		elif self.room['status'] != 'playing' and self.players:
			for player in players:
				player.close()
			self.players = []
			self.you = None

	def connect(self, room_id):
		if self.room:
			# Error
			return
		self.room = RealTimeCollection(ColRoom.name, ColRoom.find_one({'_id':room_id}))
		self.add_callback(self.handle_room_status)
		# Check one time(if room do not update immediately)
		self.handle_room_status()

	def disconnect():
		# Clear callback to avoid object references to each other
		# and wait for Python to call destructor
		self.room.clear_callback()
		for player in self.players:
			player.clear_callback()
		del self._cmd_dict

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
		return self.get_ioloop_time() < self.you['deadline']

	DEFAULT_ROOM_STATUS = {
		'status': 'init',
		'turn_uid': '',
		'turn_idx': -1,
		'player_uids': [],
		'rank_idx': 1,
		'room_manager': None
	}
	def room_init(self):
		init_status = DEFAULT_ROOM_STATUS.copy().update(self._module.Default_RoomStatus)
		init_status['room_manager'] = self.your_uid
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
		sys_playerstatus = [{
			'status': 'playing',
			'room_id': self.room['_id'],
			'deadline': 0,
			'uid': uid,
			'player_idx': idx,
			'conn': False
		} for idx, uid in enumerate(player_uids)]
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
		for player in self.players:
			player.close()
		self.players = []
		self.you = None
		room_status = DEFAULT_ROOM_STATUS.copy()
		room_status.update({'player_uids': player_uids})
		self.room.update(room_status)

	def signin_game(self):
		new_player_uids = list(self.room['player_uids'])
		new_player_uids.append(self.your_uid)
		self.room.update({'player_uids': new_player_uids})

	def signout_game(self):
		new_player_uids = list(self.room['player_uids'])
		new_player_uids.remove(self.your_uid) if self.your_uid in new_player_uids else None
		self.room.update({'player_uids': new_player_uids})

	def change_room_manager(self, uid):
		self.room.update({'room_manager': uid})

	def _deadline_handler(self, uid, dltime, callback *a, **kw):
		player = self.get_player_by_uid(uid)
		if player and player['deadline'] == dltime:
			callback(*a, **kw)

	def set_deadline(self, uid, delay, callback, *a, **kw):
		dltime = self.get_ioloop_time() + delay
		player = next(x for x in self.players if x['uid'] == uid)
		player.update({'deadline': dltime})

		IOLoop.current().add_timeout(dltime+TIMEOUT_DELAY_SEC,
										self._deadline_handler,uid, dltime, callback, *a, **kw)

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
