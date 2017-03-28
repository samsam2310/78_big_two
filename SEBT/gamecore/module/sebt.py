# -*- coding: utf-8 -*-

""" sebt gane core
"""

from __future__ import absolute_import, print_function, unicode_literals


from ..controller import Command


def draw(data, controller):
	pass

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

'turn_uid': '',
    'turn_idx': -1,
    

Default_RoomStatus = {
	'throw_card_uesr_idx': -1,
    'card_on_table': [],
    'deck': [],
    'deadwood': [],
    'rank_idx': 0,
    'playing_user_num': 0
}

Default_PlayerStatus {
	'hand': [],
    'rank': 0
}