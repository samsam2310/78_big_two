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


Default_RoomStatus = {
	'throw_card_uesr_uid': '',
	'card_on_table': [],
	'deck': [],
	'deck_num': 0,
	'deadwood': []
}

Default_PlayerStatus {
	'uid': 0,
	'hands': [],
	'rank': 0
}


def draw(data, controller, uid=None):
	player = controller.get_player_by_uid(uid) if uid else controller.you
	controller.clear_deadline(player['uid'])
	deck_list = controller.room['deck']
	room_update = {}
	if len(deck_list) == 0:
		# shuffle the deadwood
		deck = Deck(controller.room['deadwood'])
		deck.shuffle()
		room_update['deadwood'] = []
	else:
		deck = Deck(deck_list)
	new_hands = list(player['hands'])
	new_hands.append(deck.draw())
	room_update['deck'] = deck.copy()
	controller.room.update(room_update)

	player.update({'hands': new_hands})
	if new_hands == HAND_NUM_LIMIT:
		# Gameover
		controller.gameover_by_uid(uid, rank_opt=controller.RANK_LOSS)
	else:
		# Next one
		controller.next_player_turn_by_uid(uid)

def _update_hand_and_end_the_turn(player, data, controller):
	new_hands = [c for c in player['hands'] if c not in data['cards']]
	player.update({'hands': new_hands})
	if len(new_hands) == 0:
		controller.gameover_by_uid(player['uid'])
	else:
		controller.next_player_turn_by_uid(player['uid'])

def throw(data, controller, uid=None):
	player = controller.get_player_by_uid(uid) if uid else controller.you
	controller.room.update({
			'card_on_table': data['cards'],
			'throw_card_uesr_uid': player['uid']
		})
	_update_hand_and_end_the_turn(player, data, controller)

def change(data, controller, uid=None):
	player = controller.get_player_by_uid(uid) if uid else controller.you
	new_cards_list = data['cards'] + controller.room['card_on_table']
	controller.room.update({
			'card_on_table': new_cards_list,
			'throw_card_uesr_uid': player['uid']
		})
	_update_hand_and_end_the_turn(player, data, controller)

def is_card_yours(data, controller):
	hands = controller.you['hands']
	return any(c in hands for c in data['cards'])

def is_cardset_greater(data, controller):
	new_cards = bigtwo.get_cardset_from_string_list(data['cards'])
	if not new_cards:
		return False
	old_cards = controller.room['card_on_table']
	b = bigtwo.get_cardset_from_string_list(old_cards) if len(old_cards) else None
	return bigtwo.is_cardset_greater(a,b) if b else True

def is_valid_cardset_after_change(data, controller):
	if len(data['cards']) == 0:
		return False
	new_cards_list = data['cards'] + controller.room['card_on_table']
	new_cards = bigtwo.get_cardset_from_string_list(new_cards_list)
	return bool(new_cards)

def is_playing(data, controller):
	return controller.is_your_status('playing')

Command_list = []

cmd_draw = Command('draw', draw)
Command_list.append(cmd_draw)

cmd_throw = Command('throw', throw)
cmd_throw.add_permission_checker(is_card_yours)
Command_list.append(cmd_throw)

cmd_change = Command('change', change)
cmd_change.add_permission_checker(is_card_yours)
Command_list.append(cmd_change)

for cmd in Command_list:
	cmd.add_permission_checker(is_playing)

def start_game_status(player_uids, sys_roomstatus, sys_playerstatus, controller):
	deck_num = len(player_uids) * HAND_NUM_LIMIT // 52 + 1
	deck = Deck(multiple=deck_num)
	deck.shuffle()
	for idx, uid in enumerate(uplayer_uids):
		player_status = Default_PlayerStatus.copy().update({
			'hands': list(deck.draw_many(INIT_HAND_NUM))
		})
		playing_status.update(sys_playerstatus[idx])
		res = ColPlayer.insert_one(player_status)
		player = RealTimeCollection(ColPlayer.name, ColPlayer.find_one(res.inserted_id))
		controller.players.append(player)
		if controller.your_uid == uid:
			controller.you = player
	first_card = deck.draw()
	room_status = {
		'card_on_table': [first_card],
		'deck': deck.copy(),
		'deck_num': deck_num,
		'deadwood': [],
		'throw_card_user_idx': -1
	}
	room_status.update(sys_roomstatus)
	controller.room.update(room_status)

def time_is_up(uid, controller):
	if len(controller.room['card_on_table']) == 0:
		# Player must throw one of it's hands
		player = controller.get_player_by_uid(uid)
		throw({'cards': player['hands'][:1]}, controller, uid)
	else:
		# Draw a card
		draw({}, controller, uid)

def start_turn_by_player_idx(idx, controller):
	if 
	uid = controller.player[idx]['uid']
	controller.set_deadline(uid, ROUND_SEC, time_is_up, uid, controller)

def gameover_by_uid(uid, sys_roomstatus, sys_playerstatus, controller):
	player = controller.get_player_by_uid(uid)
	sys_roomstatus.update({
			'deadwood': list(self.room['deadwood']) + list(player['hands'])
		})
	sys_playerstatus.update({
			'hands': []
		})
	controller.room.update(sys_roomstatus)
	player.update(sys_playerstatus)
	controller.next_player_turn_by_uid(uid)

def last_one_player_by_idx(idx, controller):
	uid = controller.players[idx]['uid']
	controller.gameover_by_uid(uid)
