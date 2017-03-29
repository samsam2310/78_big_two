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
				yield cls._classUpdate(slog['colname'], slog['obj_id'], slog['ts'])
			yield gen.sleep(0.1)


	def __init__(self, colname, data, on_updata=None):
		self._colname = colname
		self._obj_id = data['_id']
		self._data = data
		self._ts = 0
		self._on_upodate = on_updata
		key = colname + str(self._obj_id)
		if not self._callback_dict.get(key):
			self._callback_dict[key] = set()
		self._callback_dict[key].add(self._handle_update)

	def close(self, *a, **kw):
		if not self._obj_id:
			return
		key = self._colname + str(self._obj_id)
		s = self._callback_dict.get(key)
		s.remove(self._handle_update) if s else None
		self._callback_dict.pop(key) if (s and len(s) == 0) else None
		self._colname = self._obj_id = self._data = None

	def _handle_update(self, data, ts):
		if not data:
			return self.close()
		if ts > self._ts:
			self._data = data
			self._ts = ts
			self._on_update(data) if self._on_upodate else None

	def update(self, update_data):
		self._db[self._colname].update_one({'_id': self._obj_id}, { '$set': update_data})
		self._data.update(update_data)
		self._ts = int(time.mktime(datetime.datetime.utcnow().timetuple()))
		self.col_SL.insert_one({'colname': self._colname, 'obj_id': self._obj_id, 'ts': self._ts})
