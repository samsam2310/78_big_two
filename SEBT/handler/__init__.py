# -*- coding: utf-8 -*-

""" Handler - init.
"""

from __future__ import absolute_import, print_function, unicode_literals

from .game import GameHandler, GameSocketHandler
from .room import RoomHandler


__all__ = ['route']

route = [
        (r'/room', RoomHandler),
        (r'/game', GameHandler),
        (r'/gamesocket', GameSocketHandler),
    ]
