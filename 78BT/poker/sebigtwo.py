# -*- coding: utf-8 -*-

""" poker - bigtwo
"""

from . import POKER_CARD


def to_number(alpha, ATO1=False, bigtwo=False):
    if alpha == 'T':
        return 10
    if alpha == 'J':
        return 11
    if alpha == 'Q':
        return 12
    if alpha == 'K':
        return 13
    if alpha == 'A':
        return 1 if ATO1 else 14
    n = int(alpha)
    if n == 2 and bigtwo:
        n = 15
    return n

def comp_poker(a, b, bigtwo=False):
    if a == b:
        return 0
    if a[1] == b[1]:
        return -1 if a[0] < b[0] else 1
    return -1 if to_number(a[1], bigtwo=bigtwo) < to_number(b[1], bigtwo=bigtwo) else 1

def check_straight(cards, l=5):
    for i in range(l-1):
        if to_number(cards[i][1], i==0)+1 != to_number(cards[i+1][1]):
            return False
    return True

def check_flush(cards, l=5):
    for i in range(l-1):
        if cards[i][0] != cards[i+1][0]:
            return False
    return True


SINGLE = 0
PAIR = 1
FULLHOUSE = 2
STRAIGHT = 3
FOUROFAKIND = 4
STRAIGHTFLUSH = 5
DRAGON = 6

class CardSet():
    def __init__(self, cards):
        for c in cards:
            if not c in POKER_CARD:
                raise Exception()
        self.check_type(cards)
        if self._type == -1:
            raise Exception()
        
    def check_type(self, unsorted_cards):
        self._type = -1
        self._big = ''
        cards = sorted(unsorted_cards, comp_poker)
        print(cards)
        if len(cards) == 1:
            self._type = SINGLE
            self._big = cards[0]
            return
        elif len(cards) == 2 and cards[0][1] == cards[1][1]:
            self._type = PAIR
            self._big = cards[1]
            return
        elif len(cards) == 5:
            if cards[0][1] == cards[1][1] and cards[3][1] == cards[4][1]:
                if cards[1][1] == cards[2][1]:
                    self._type = FULLHOUSE
                    self._big = cards[2]
                    return
                elif cards[2][1] == cards[3][1]:
                    self._type = FULLHOUSE
                    self._big = cards[4]
                    return

            if card[1][1] == card[2][1] and card[2][1] == card[3][1]:
                if card[0][1] == card[1][1]:
                    self._type = FOUROFAKIND
                    self._big = cards[3]
                    return
                elif card[3][1] == card[4][1]:
                    self._type = FOUROFAKIND
                    self._big = cards[4]
                    return

            if check_straight(cards):
                self._big = cards[4] if cards[0][1] != '2' else cards[0]
                if check_flush(cards):
                    self._type = STRAIGHTFLUSH
                    return
                else:
                    self._type = STRAIGHT
                    return
        elif len(cards) == 13:
            if check_straight(cards, 13):
                self._type = DRAGON
                self._big = cards[12]
                return

    @staticmethod
    def comp(a, b):
        if a._type == b._type:
            return 1 if comp_poker(a._big, b._big, bigtwo=True) else 0
        elif a._type >= FOUROFAKIND or b._type >= FOUROFAKIND:
            return 1 if a._type < b._type else 0
        return -1

    @classmethod
    def gen(cls, cards):
        try:
            return cls(cards)
        except Exception:
            return None
