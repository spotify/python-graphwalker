# -*- coding: utf-8 -*-
# Copyright (c) 2013 Spotify AB
import logging
import unittest

from graphwalker import tapping


class TargetMock(object):
    def __init__(self):
        self.logs = []

    def log(self, origin, message):
        self.logs.append((origin, message))


class TestStreamTap(unittest.TestCase):
    class MockObj(object):
        def __init__(self):
            self.fleb = '<z>'

    def build(self):
        st = tapping.StreamTap(TargetMock(), 'fleb', self.MockObj())
        return st

    def test_ctor_smoke(self):
        tapping.StreamTap('target', 'name', object())

    def test_install(self):
        st = self.build()
        self.assertEqual(st.obj.fleb, '<z>')
        st.install()
        self.assertEqual(st.obj.fleb, st)
        self.assertEqual(st.saved, '<z>')

    def test_remove(self):
        st = self.build()
        st.saved = '<w>'
        self.assertEqual(st.obj.fleb, '<z>')
        st.remove()
        self.assertEqual(st.obj.fleb, '<w>')

    def test_write(self):
        st = self.build()
        st.write('foo')
        self.assertEqual(st.reporter.logs, [('fleb', 'foo')])


class TestLogTap(unittest.TestCase):
    class LoggerMock(object):
        def __init__(self):
            self.calls = []

        def addHandler(self, what):
            self.calls.append(('add', what))

        def removeHandler(self, what):
            self.calls.append(('rem', what))

    def test_ctor_smoke(self):
        tapping.LogTap('target')

    def build(self):
        lm = self.LoggerMock()
        lt = tapping.LogTap(TargetMock())
        lt.get_root_logger = lambda: lm
        return lt, lm

    def test_install(self):
        lt, lm = self.build()
        lt.install()
        self.assertEqual(lm.calls, [('add', lt)])

    def test_remove(self):
        lt, lm = self.build()
        lt.remove()
        self.assertEqual(lm.calls, [('rem', lt)])

    def test_emit(self):
        lt, lm = self.build()
        lt.emit(logging.makeLogRecord({
            'name': 'foo', 'level': logging.INFO, 'msg': 'meh'}))
        self.assertEqual(lt.target.logs, [('foo', 'meh')])
