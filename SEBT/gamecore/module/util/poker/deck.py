# -*- coding: utf-8 -*-

""" poker - card
"""

from __future__ import absolute_import, print_function, unicode_literals

import random


POKER_CARD = []
ALPHA = ['T','J','Q','K','A']
for i in range(4):
    for j in range(2,15):
        POKER_CARD.append('%d%s' % (i, j if j < 10 else ALPHA[j-10]))


class Deck():
    def __init__(self, cards=None, mutiple=1):
        self._cards = list(cards) if cards else POKER_CARD*mutiple

    def shuffle(self):
        random.shuffle(self._cards)

    def draw(self):
        c = self.draw_many(1)
        return c[0] if c else None

    def draw_many(self, n):
        if len(self._cards) < n:
            return None
        cs = self._cards[:n]
        self._cards = self._cards[n:]
        return cs

    def copy(self):
        return list(self._cards)
