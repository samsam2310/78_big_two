# -*- coding: utf-8 -*-

""" poker - cardset
"""

from __future__ import absolute_import, print_function, unicode_literals

from .card import Card


class BaseType():
    def __init__(self, cards, checked=True):
        if checked:
            self._cards = list(cards)
            return
        for card in cards:
            if not isinstance(card, Card):
                raise ValueError('Not an instance of Card.')
        self._cards = sorted(cards)
        if not self.check_type(self._cards):
            raise ValueError('Type Error.')

    @classmethod
    def check_type(cls, cards):
        return True

    def to_point(self):
        return 0

    @classmethod
    def get(cls, cards):
        # cards must be sorted.
        if cls.check_type(cards):
            return cls(cards)
        return None


class TypeSingle(BaseType):
    @classmethod
    def check_type(cls, cards):
        return len(cards) == 1

    def to_point(self):
        return self._cards[0].to_point()

class TypePair(BaseType):
    @classmethod
    def check_type(cls, cards):
        return len(cards) == 2 and cards[0].to_number() == cards[1].to_number()

    def to_point(self):
        return self._cards[0].to_point()

class TypeFullHouse(BaseType):
    @classmethod
    def check_type(cls, cards):
        number = [x.to_number() for x in cards]
        return (
                len(cards) == 5 and
                number[0] == number[1] and number[3] == number[4] and
                ( number[2] == number[1] or number[2] == number[3] )
            )

    def to_point(self):
        if self._cards[2].to_number() == self._cards[1].to_number():
            return self._cards[2].to_point()
        return self._cards[4].to_point()

class TypeStraight(BaseType):
    @classmethod
    def check_type(cls, cards):
        number = [x.to_number() for x in cards]
        return (
                len(cards) == 5 and (
                    any(number[i]+1==number[i+1] for i in range(4)) 
                    or
                    number[0] == 1 and number[1] == 10 and
                    any(number[i]+1==number[i+1] for i in range(3))
                )
            )

    def to_point(self):
        return max(x.to_point() for x in self._cards)

class TypeFlush(BaseType):
    @classmethod
    def check_type(cls, cards):
        fid = cards[0].to_suit_id()
        return (
                len(cards) == 5 and
                any(x.to_suit_id() == fid for x in cards)
            )

    def to_point(self):
        return max(x.to_point() for x in self._cards)

class TypeStraightFlush(TypeStraight):
    @classmethod
    def check_type(cls, cards):
        return (
                TypeStraight.check_type(cards) and
                TypeFlush.check_type(cards)
            )

class FOUROFAKIND(BaseType):
    @classmethod
    def check_type(cls, cards):
        number = [x.to_number() for x in cards]
        return len(cards) == 5 and (
                number.count(number[0]) == 4 or
                number.count(number[4]) == 4
            )

    def to_point(self):
        if self._cards[0].to_number() == self._cards[1].to_number():
            return self._cards[3].to_point()
        return self._card[4].to_point()

class TypeDragon(TypeStraight):
    @classmethod
    def check_type(cls, cards):
        number = [x.to_number() for x in cards]
        return (
                len(cards) == 13 and
                any(number[i]+1==number[i+1] for i in range(12))
            )
