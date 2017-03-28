# -*- coding: utf-8 -*-

""" game controller
"""

from __future__ import absolute_import, print_function, unicode_literals

from tornado.ioloop import IOLoop


class Controller():
	def __init__(self, room_status, your_status, players_status):
		self.room = room_status
		self.you = your_status
		self.players = players_status
		self._cmd_dict = dict()
		self._add_default_command()

	def _add_default_command(self):
		pass

	def call(self, cmd, data):
		self._cmd_dict[cmd](data)

	def add_command(self, cmd_obj):
		self._com_dict[cmd_obj.name] = cmd_obj

	def is_room_manager(self):
		return self.room['room_manager'] == self.you['_id']

	def is_room_status(self, sts):
		return self.room['status'] == sts

	def is_your_status(self, sts):
		return self.you['status'] == sts

	def is_before_your_deadline(self):
		pass

	def start_game(self):
		pass

	def stop_game(self):
		pass

	def signin_game(self):
		pass

	def signout_game(self):
		pass

	def change_room_manager(self):
		pass

	def add_deadline(self):
		pass

	def next_one(self):
		pass

	def game_over(self):
		pass

	def get_ioloop_time(self):
		pass
