# -*- coding: utf-8 -*-

""" bigtwo
"""

from __future__ import absolute_import, print_function, unicode_literals

from .poker.cardset import *
from .poker.card import Card


class BigTwoCard(Card):
	def to_point(self):
		n = self.to_number()
		n = n+13 if n<=2 else n
		return self.to_suit_id()*100 + n

Allow_Type = [  TypeSingle, TypePair,
            	TypeFullHouse, TypeStraight, TypeFlush,
            	TypeFourOfAKind, TypeStraightFlush, TypeDragon ]
MONSTER_TYPE_ID = 5

def get_cardset_from_string_list(card_strings):
	try:
		cards = sorted(BigTwoCard(x) for x in card_strings)
	except ValueError:
		return None
	for idx, set_type in enumerate(Allow_Type):
		if set_type.check_type(cards):
			return set_type(cards, idx)
	return None

def is_type_greater_then(a, b):
	if a.typeid == b.typeid:
		return a.to_point() > b.to_point()
	return a.typeid >= MONSTER_TYPE_ID and a.typeid > b.typeid
