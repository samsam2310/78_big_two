# -*- coding: utf-8 -*-

""" game controller command
"""

from __future__ import absolute_import, print_function, unicode_literals


class Command():
	def __init__(self, cmd, cmd_fun):
		self._cmd = cmd
		self._cmd_fun = cmd_fun
		self._permission_checkers = []

	def __call__(self, data, controller):
		if any(fun(data, controller) for fun in self._permission_checkers):
			self._cmd_fun(data, controller)
		else:
			self._forbidden(data, controller)

	def _forbidden(self, *a, **kwarg):
		pass

	@property
	def name(self):
		return self._cmd

	def add_permission_checker(self, fun):
		self._permission_checker.append(fun)
