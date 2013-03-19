# -*- coding: utf-8 -*-
# Copyright (c) 2013 Spotify AB
import unittest

from graphwalker import stopcond


class TestSeconds(unittest.TestCase):
    def test_ctor_smoke(self):
        self.assertFalse(stopcond.Seconds().start(None))
        self.assertFalse(stopcond.Seconds(20).start(None))
        self.assertFalse(stopcond.Seconds(timeout=20).start(None))

    def test_empty_done(self):
        self.assertTrue(stopcond.Seconds(0).start(None))

    def test_api(self):
        ec = stopcond.Seconds(8).start(None)
        ec.add(('cat', 'dog', ()))
        self.assert_(type(ec.progress()) is str)

    def test_step_through(self):
        t, ec = 20, stopcond.Seconds(8)
        ec.clock = lambda: t
        self.assertFalse(ec.start(None))

        for t, expect in ((23, False), (27, False), (28, True), (29, True)):
            self.assertEqual(bool(ec), expect)


class TestSeenSteps(unittest.TestCase):
    def test_ctor_smoke(self):
        stopcond.SeenSteps()
        stopcond.SeenSteps(*'abc')

    def test_ctor_args(self):
        self.assertEqual(stopcond.SeenSteps().targets, set([]))
        self.assertEqual(stopcond.SeenSteps(*'abc').targets, set('abc'))

    def test_empty_done(self):
        self.assertTrue(stopcond.SeenSteps().start(None))

    def test_api(self):
        ec = stopcond.SeenSteps(*'abc').start(None)
        ec.add(('cat', 'dog', ()))
        self.assert_(type(ec.progress()) is str)

    def test_step_through(self):
        ec = stopcond.SeenSteps(*'abc').start(None)
        self.assertFalse(ec)
        ec.add('xa')
        self.assertFalse(ec)
        ec.add('xb')
        self.assertFalse(ec)
        ec.add('xc')
        self.assertTrue(ec)


class TestCountSteps(unittest.TestCase):
    def test_ctor_smoke(self):
        self.assertFalse(stopcond.CountSteps().start(None))
        self.assertFalse(stopcond.CountSteps(123).start(None))
        self.assertFalse(stopcond.CountSteps(steps=123).start(None))

    def test_zero_done(self):
        self.assertTrue(stopcond.CountSteps(0).start(None))

    def test_api(self):
        ec = stopcond.CountSteps().start(None)
        ec.add(('cat', 'dog', ()))
        self.assert_(type(ec.progress()) is str)

    def test_step_through(self):
        ec = stopcond.CountSteps(3).start(None)
        self.assertFalse(ec)
        ec.add('xa')
        self.assertFalse(ec)
        ec.add('xb')
        self.assertFalse(ec)
        ec.add('xc')
        self.assertTrue(ec)


class g:
    V = {'a': ()}
    E = {'e': ()}


class TestCoverage(unittest.TestCase):
    def test_ctor_smoke(self):
        self.assertFalse(stopcond.Coverage().start(g))
        self.assertFalse(stopcond.Coverage(edges=10).start(g))
        self.assertFalse(stopcond.Coverage(verts=20).start(g))
        self.assertFalse(stopcond.Coverage(edges=10, verts=20).start(g))
        self.assertFalse(stopcond.Coverage(edges=10, vertices=20).start(g))

    def test_zero_done(self):
        ec = stopcond.Coverage()
        ec.edge_cov = 0.0
        self.assertTrue(ec.start(g))

    def test_api(self):
        ec = stopcond.Coverage().start(g)
        ec.add(('cat', 'dog', ()))
        self.assert_(type(ec.progress()) is str)

    def test_step_through(self):
        ec = stopcond.Coverage(edges=1, verts=1).start(g)
        self.assertFalse(ec)
        ec.add('aaaa')
        self.assertFalse(ec)
        ec.add('eee')
        self.assertTrue(ec)
