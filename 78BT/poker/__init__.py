# -*- coding: utf-8 -*-

""" poker - init
"""

from __future__ import absolute_import, print_function, unicode_literals

import random


__all__ = ['Poker',]


POKER_CARD = []
ALPHA = ['T','J','Q','K','A']
for i in range(4):
    for j in range(2,15):
        POKER_CARD.append('%d%s' % (i, j if j < 10 else ALPHA[j-10]))

class Poker():
    def __init__(self, cards=None):
        if cards:
            self._cards = list(cards)
        else:
            self._cards = list(POKER_CARD)

    def wash(self):
        random.shuffle(self._cards)

    def pick(self):
        c = self.pick_many(1)
        return c[0] if c else None

    def pick_many(self, n):
        if len(self._cards) < n:
            return None
        c = self._cards[:n]
        self._cards = self._cards[n:]
        return c

    def to_list(self):
        return list(self._cards)
