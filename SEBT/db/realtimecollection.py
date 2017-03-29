# -*- coding: utf-8 -*-

""" DB - real time collection object
"""

from tornado import gen
from tornado.gen import Return
from pymongo.errors import CollectionInvalid
from datatime import datatime

import time
import pymongo


STATUS_LOG_COL_SIZE = 10 * 1024**2

class RealTimeCollection():
	_callback_dict = dict()

	@classmethod
	def classInit(cls, db):
		cls._db = db
		try:
			cls._db.create_collection('StatusLog', size=STATUS_LOG_COL_SIZE, capped=True)
		except CollectionInvalid:
			pass
		cls._col_SL = cls.db['StatusLog']

	@classmethod
	@gen.coroutine
	def _classUpdate(cls, colname, obj_id, ts):
		callback_set = cls._callback_dict.get(colName + str(obj_id))
		if not callback_set:
			raise Return(None)
		data = cls._db[colname].find_one({'_id': obj_id})
		for callback in callback_set.copy():
			yield gen.Task(callback, data, ts)

	@classmethod
	@gen.coroutine
	def syncLoop(cls):
		ts = datetime.utcnow()
		cursor = cls._col_SL.find({'ts': {'$gt': ts}}, cursor_type=pymongo.CursorType.TAILABLE)
		while cursor.alive:
			for slog in cursor:
				yield cls._classUpdate(slog['colname'], slog['obj_id'])
			yield gen.sleep(0.1)

	def __init__(self, colname, data):
		self._colname = colname
		self._obj_id = data['_id']
		self._on_upodates = []
		key = colname + str(self._obj_id)
		if not self._callback_dict.get(key):
			self._callback_dict[key] = set()
		self._callback_dict[key].add(self._handle_update)
		self._data = self._db[colname].find_one({'_id': data['_id']})

	def __getitem__(self, key):
		return self._data[key]

	def close(self):
		if not self._obj_id:
			return
		self._colname = self._obj_id = self._data = None
		key = self._colname + str(self._obj_id)
		fun_set = self._callback_dict.get(key)
		fun_set.remove(self._handle_update) if fun_set else None
		self._callback_dict.pop(key) if (fun_set and len(fun_set) == 0) else None

	def add_callback(self, callback):
		self._on_updates.append(callback)

	def clear_callback(self):
		self._on_updates = []

	def _handle_update(self, data):
		if not data:
			return self.close()
		self._data = data
		for fun in self._on_upodates:
			fun(data)

	def update(self, update_data):
		self._db[self._colname].update_one({'_id': self._obj_id}, { '$set': update_data})
		self._data.update(update_data)
		ts = int(time.mktime(datetime.datetime.utcnow().timetuple()))
		self.col_SL.insert_one({'colname': self._colname, 'obj_id': self._obj_id, 'ts': ts})
