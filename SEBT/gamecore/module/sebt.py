# -*- coding: utf-8 -*-

""" sebt gane core
"""

from __future__ import absolute_import, print_function, unicode_literals


from ...db import RealTimeCollection, ColPlayer
from ..controller import Command
from .util import bigtwo
from .util.poker.deck import Deck


# For controller
ROUND_SEC = 30
ROOM_PLAYER_LIMIT = 7

# For module
INIT_HAND_NUM = 5
HAND_NUM_LIMIT = 13


def draw(data, controller, uid=None):
	player = next(x for x in self.players if x['uid'] == uid) if uid else controller.you
	controller.clear_deadline(player['uid'])
	# TODO

def throw(data, controller):
	pass

def change(data, controller):
	pass

def is_card_yours(data, controller):
	your_card = controller.you['hand']
	return any(c in your_card for c in data)

def is_playing(data, controller):
	return controller.is_your_status('playing')

Command_list = []

cmd_draw = Command('draw', draw)
Command.append(cmd_draw)

cmd_throw = Command('throw', throw)
cmd_throw.add_permission_checker(is_card_yours)
Command.append(cmd_throw)

cmd_change = Command('change', change)
cmd_change.add_permission_checker(is_card_yours)
Command.append(cmd_change)

for cmd in Command_list:
	cmd.add_permission_checker(is_playing)


Default_RoomStatus = {
	'throw_card_uesr_idx': -1,
	'card_on_table': [],
	'deck': [],
	'deadwood': [],
	'rank_idx': 0
}

# Default_PlayerStatus {
# 	'hand': [],
# 	'rank': 0
# }

def start_game_status(playing_user_uids, sys_roomstatus, sys_playerstatus, controller):
	deck = Deck()
	deck.shuffle()
	for uid in playing_user_uids:
		player_status = {
			'uid': uid,
			'hand': list(deck.draw_many(INIT_HAND_NUM)),
			'rank': 0
		}
		playing_status.update(sys_playerstatus)
		res = ColPlayer.insert_one(player_status)
		player = RealTimeCollection(ColPlayer.name, ColPlayer.find_one(res.inserted_id))
		controller.players.append(player)
		if controller.your_uid == uid:
			controller.you = player
	first_card = deck.draw()
	room_status = {
		'card_on_table': [first_card],
		'deck': deck.copy(),
		'deadwood': [],
		'throw_card_user_idx': -1,
		'rank_idx': 0,
	}
	room_status.update(sys_roomstatus)
	controller.room.update({'$set': room_status})

def time_is_up(uid, controller):
	draw({}, controller, uid)

def start_turn(uid, controller):
	controller.set_deadline(uid, ROUND_SEC, time_is_up, uid, controller)
