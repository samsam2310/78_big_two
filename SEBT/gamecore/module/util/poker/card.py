# -*- coding: utf-8 -*-

""" poker - card
"""

from __future__ import absolute_import, print_function, unicode_literals


from .dack import POKER_CARD


class Card():
    def __init__(self, card):
        if not card in POKER_CARD:
            raise ValueError('Card invaild: %s' % c)
        self._card = card

    # Get the nunber of the card, not the point(point may consider about Suit)
    def to_number(self):
        alpha = self._card[1]
        if alpha == 'T':
            return 10
        if alpha == 'J':
            return 11
        if alpha == 'Q':
            return 12
        if alpha == 'K':
            return 13
        if alpha == 'A':
            return 1
        n = int(alpha)
        return n

    def to_suit_id(self):
        return int(self._card[0])

    def to_point(self):
        alpha = self._card[1]
        n = self.to_number()
        if n == 1:
            return 14
        return n

    def to_order(self):
        return self.to_suit_id()*100 + self.to_number()

    def __eq__(self, b):
        return self._card == b._card
    def __ne__(self, b):
        return not self.__eq__(b)
    def __lt__(self, b):
        return self.to_order() < b.to_order()
    def __le__(self, b):
        return self.to_order() <= b.to_order()
    def __gt__(self, b):
        return self.to_order() > b.to_order()
    def __ge__(self, b):
        return self.to_order() >= b.to_order()
