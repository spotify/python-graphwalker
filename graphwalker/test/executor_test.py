# -*- coding: utf-8 -*-
# Copyright (c) 2013 Spotify AB
import unittest

from graphwalker import executor


class Fail(AssertionError):
    def __eq__(self, other):
        return (isinstance(other, AssertionError) and
                self.args == other.args)


class Dummy(object):
    def __init__(self):
        self.calls = []

    def __getattr__(self, k):
        def f(*al, **kw):
            self.calls.append((k, al, kw))
            assert k != 'fail', 'fail!'
        f.__name__ = k
        return f


class Recoverer(Dummy):
    def step_end(self, *al, **kw):
        self.calls.append(('step_end', al, kw))
        return 'RECOVER'


class TestExecutor(unittest.TestCase):
    def assertEqualList(self, l, m):
        diff = False
        for i in range(min(len(l), len(m))):
            if l[i] != m[i]:
                print i, l[i], '!=\n ', m[i]
                diff = True

        self.assertEqual(len(l), len(m))
        self.assert_(not diff, "Lists differ")

    def test_ctor_smoke(self):
        executor.Executor(None, None)

    def build(self, actorclass=None):
        e = executor.Executor((actorclass or Dummy)(), Dummy())
        e.log = Dummy()
        return e

    def test_empty_plan(self):
        self.build().run('name', [], {})

    def test_simple_plan(self):
        self.build().run('name', ['foo', 'bar', 'baz'], {})

    def test_empty_plan_reporter(self):
        e = self.build()
        e.run('name', [], {'ctx': 1})
        self.assertEqual(
            e.reporter.calls,
            [('update', ({'ctx': 1, 'actor': e.actor},), {}),
             ('initiate', ('name',), {}),
             ('finalize', (None,), {})])

    def test_empty_plan_actor(self):
        e = self.build()
        e.run('name', [], {'ctx': 1})
        self.assertEqual(
            e.actor.calls,
            [('setup', ({'ctx': 1, 'actor': e.actor},), {}),
             ('teardown', ({'ctx': 1, 'actor': e.actor},), {})])

    def test_simple_plan_reporter(self):
        e = self.build()
        e.run('name', ['foo', 'bar', 'baz'], {'ctx': 1})
        self.assertEqual(
            e.reporter.calls,
            [('update', ({'ctx': 1, 'actor': e.actor},), {}),
             ('initiate', ('name',), {}),
             ('step_begin', ('foo',), {}),
             ('step_end', ('foo', None), {}),
             ('step_begin', ('bar',), {}),
             ('step_end', ('bar', None), {}),
             ('step_begin', ('baz',), {}),
             ('step_end', ('baz', None), {}),
             ('finalize', (None,), {})])

    def test_simple_plan_actor(self):
        e = self.build()
        e.run('name', [(0, 'foo'), (1, 'bar'), (2, 'baz')], {'ctx': 1})
        self.assertEqual(
            e.actor.calls,
            [('setup', ({'ctx': 1, 'actor': e.actor},), {}),
             ('step_begin', ((0, 'foo'),), {}),
             ('foo', (), {}),
             ('step_end', ((0, 'foo'), None), {}),
             ('step_begin', ((1, 'bar'),), {}),
             ('bar', (), {}),
             ('step_end', ((1, 'bar'), None), {}),
             ('step_begin', ((2, 'baz'),), {}),
             ('baz', (), {}),
             ('step_end', ((2, 'baz'), None), {}),
             ('teardown', ({'ctx': 1, 'actor': e.actor},), {})])

    def test_fail_reporter(self):
        e = self.build()
        e.run('name', [(0, 'fail')], {'ctx': 1})
        self.assertEqual(
            e.reporter.calls,
            [('update', ({'ctx': 1, 'actor': e.actor},), {}),
             ('initiate', ('name',), {}),
             ('step_begin', ((0, 'fail'),), {}),
             ('step_end', ((0, 'fail'), Fail('fail!')), {}),
             ('finalize', (Fail('fail!'),), {})])

    def test_fail_actor(self):
        e = self.build()
        e.run('name', [(0, 'fail')], {'ctx': 1})
        self.assertEqual(
            e.actor.calls,
            [('setup', ({'ctx': 1, 'actor': e.actor},), {}),
             ('step_begin', ((0, 'fail'),), {}),
             ('fail', (), {}),
             ('step_end', ((0, 'fail'), Fail('fail!'),), {}),
             ('teardown', ({'ctx': 1, 'actor': e.actor},), {})])

    def test_fail_debug_trace(self):
        e = self.build()
        e.debugger = Dummy()
        e.run('name', [(0, 'fail')], {'ctx': 1})
        self.assertEqual(e.debugger.calls, [('set_trace', (), {})])

    def test_fail_debug_call(self):
        e = self.build()
        calls = []
        e.debugger = lambda: calls.append('*call*')
        e.run('name', [(0, 'fail')], {'ctx': 1})
        self.assertEqual(calls, ['*call*'])

    def test_pass_no_debug_trace(self):
        e = self.build()
        e.debugger = Dummy()
        e.run('name', [(0, 'fine')], {'ctx': 1})
        self.assertEqual(e.debugger.calls, [])

    def test_pass_no_debug_call(self):
        e = self.build()
        calls = []
        e.debugger = lambda: calls.append('*call*')
        e.run('name', [(0, 'fine')], {'ctx': 1})
        self.assertEqual(calls, [])

    def test_recover_reporter(self):
        e = self.build(Recoverer)
        e.run('name', [(0, 'fail'), (1, 'cont')], {'ctx': 1})
        l = [('update', ({'ctx': 1, 'actor': e.actor},), {}),
             ('initiate', ('name',), {}),
             ('step_begin', ((0, 'fail'),), {}),
             ('step_end', ((0, 'fail'), Fail('fail!')), {}),
             ('step_begin', ((1, 'cont'),), {}),
             ('step_end', ((1, 'cont'), None), {}),
             ('finalize', (None,), {})]
        self.assertEqual(e.reporter.calls, l)

    def test_recover_actor(self):
        e = self.build(Recoverer)
        e.run('name', [(0, 'fail'), (1, 'cont')], {'ctx': 1})
        l = [('setup', ({'ctx': 1, 'actor': e.actor},), {}),
             ('step_begin', ((0, 'fail'),), {}),
             ('fail', (), {}),
             ('step_end', ((0, 'fail'), Fail('fail!')), {}),
             ('step_begin', ((1, 'cont'),), {}),
             ('cont', (), {}),
             ('step_end', ((1, 'cont'), None), {}),
             ('teardown', ({'ctx': 1, 'actor': e.actor},), {})]
        self.assertEqualList(e.actor.calls, l)
