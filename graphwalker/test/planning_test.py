# -*- coding: utf-8 -*-
# Copyright (c) 2013 Spotify AB
import cStringIO
import signal
import unittest

from graphwalker import planning


class Thing(tuple):
    id = property(lambda self: self[0])
    name = property(lambda self: self[1])
    outgoing = property(lambda self: self[2])
    incoming = property(lambda self: self[3])
    src = property(lambda self: self[2])
    tgt = property(lambda self: self[3])
    weight = property(lambda self: self[4] if len(self) > 4 else None)


class G(object):
    def __init__(self, V, E):
        self.V, self.E = V, E

    del_vert = lambda s, v: v
    eulerize = lambda s: s
    copy = lambda s: s

    def vert_degrees(self):
        I = dict((v, 0) for v in self.V)
        O = dict(I)
        for edge in self.E.values():
            O[edge.src] += 1
            I[edge.tgt] += 1
        return I, O

vert, edge = Thing('aa'), Thing('eeaa')
V, E = {'a': vert}, {'e': edge}
g = G(V, E)


def build_graph(spec):
    V = dict((v, Thing((v, v, []))) for v in sorted(set(spec)))
    E = dict((f + t, Thing((f + t, f + t, f, t))) for f, t in spec.split())
    for edge in sorted(E.values()):
        V[edge.src].outgoing.append(edge)
    return G(V, E)


class EhmNo(object):
    __nonzero__ = lambda s: False
    add = lambda s, x: False
    start = lambda s, *al: s


class TestPlanner(unittest.TestCase):
    def test_ctor_smoke(self):
        self.assert_(planning.Planner())

    def test_setup_results(self):
        p = planning.Planner()
        V, E, plan, v = p._setup(g, EhmNo().start(None), 'a', '<ctx>')
        self.assert_(V is g.V)
        self.assert_(E is g.E)
        self.assert_(v is vert)

        self.assert_(p.g is g)
        self.assert_(plan is p.plan)
        self.assert_(v is p.vert)

    def test_setup_rng_none(self):
        calls = []

        class Sub(planning.Planner):
            randcls = lambda *al, **kw: calls.append((al, kw))

        p = Sub()
        self.assertEqual(calls, [((p, None,), {})])

    def test_setup_rng_some(self):
        calls = []

        class Sub(planning.Planner):
            randcls = lambda *al, **kw: calls.append((al, kw))

        p = Sub(seed='cthulhu')
        self.assertEqual(calls, [((p, 'cthulhu',), {})])

    def test_forced_plan(self):
        g = build_graph('ab bc cd de ef fd')
        p = planning.Planner(seed='cthulhu')
        p._setup(g, EhmNo(), 'a', '<ctx>')
        self.assertEqual(p.plan, [])
        p.forced_plan()
        self.assertEqual([s[0] for s in p.plan], ['ab', 'b'])

    def test_visit_own(self):
        p = planning.Planner(seed='cthulhu')
        p.stop, p.plan = set(), []
        p.visit('moo')
        self.assert_('moo' in p.stop)
        self.assertEqual(p.plan, ['moo'])

    def test_visit_not_own(self):
        p = planning.Planner(seed='cthulhu')
        p.stop, p.plan, extrap = set(), [], []
        p.visit('moo', extrap)
        self.assert_('moo' in p.stop)
        self.assertEqual(p.plan, [])
        self.assertEqual(extrap, ['moo'])

    def test_step(self):
        visited, plan = [], []

        class g:
            V = {'to': 'dest'}

        class e:
            src = 'fm'
            tgt = 'to'

        class v:
            id = 'fm'

        p = planning.Planner(seed='cthulhu')
        p.stop, p.plan, p.g = set(), [], g
        p.visit = lambda thing, plan: visited.append(thing)

        result = p.step(v, e, plan)
        self.assertEqual(result, 'dest')
        self.assertEqual(visited, [e, 'dest'])
        self.assertEqual(p.plan, [])


class rng:
    def __init__(self, dice=None):
        self.calls = []
        self.dice = dice

    def choice(self, seq):
        self.calls.append(('choice', seq))
        return seq[self.dice.pop(0) if self.dice else -1]

    def uniform(self, a, b):
        self.calls.append(('uniform', a, b))
        return self.dice.pop(0) if self.dice else a + (b - a) / 2


class TestEvenRandom(unittest.TestCase):
    thiscls = planning.EvenRandom

    def test_ctor_smoke(self):
        self.assert_(self.thiscls())
        self.assert_(self.thiscls(12))
        self.assert_(self.thiscls(seed=12))

    def test_call(self):
        g = build_graph('ab bc cb')
        p = self.thiscls()
        p.rng = rng([-1, -1, -1])

        plan = zip(p(g, EhmNo(), 'a', 'context'), '012345')
        self.assertEqual(plan, [
            (g.E['ab'], '0'), (g.V['b'], '1'),
            (g.E['bc'], '2'), (g.V['c'], '3'),
            (g.E['cb'], '4'), (g.V['b'], '5'),
        ])

    def test_call_choices(self):
        g = build_graph('ab bc cb bb cc')
        p = self.thiscls()
        p.rng = rng([0, 1, 0, 1, 0])

        plan = zip(p(g, EhmNo(), 'a', 'context'), range(10))
        l = [
            (g.E['ab'], 0), (g.V['b'], 1),
            (g.E['bc'], 2), (g.V['c'], 3),
            (g.E['cb'], 4), (g.V['b'], 5),
            (g.E['bc'], 6), (g.V['c'], 7),
            (g.E['cb'], 8), (g.V['b'], 9),
        ]
        self.assertEqual(plan, l)
        calls = [
            ('choice', [g.E['ab']]),
            ('choice', [g.E['bb'], g.E['bc']]),
            ('choice', [g.E['cb'], g.E['cc']]),
            ('choice', [g.E['bb'], g.E['bc']]),
            ('choice', [g.E['cb'], g.E['cc']]),
            ('choice', [g.E['bb'], g.E['bc']]),
        ]
        self.assertEqual(p.rng.calls, calls)


class TestRandom(TestEvenRandom):
    thiscls = planning.Random

    def test_call_weighted_choices(self):
        g = build_graph('ab bc cb bb cc')
        g.E['bb'] = Thing(('bb', 'bb', 'b', 'b', '25%'))
        g.V['b'].outgoing[0] = g.E['bb']

        p = self.thiscls()
        p.rng = r = rng([0, 0.26, 0, 0.24, 1, 0])

        plan = zip(p(g, EhmNo(), 'a', 'context'), range(10))
        l = [
            (g.E['ab'], 0), (g.V['b'], 1),
            (g.E['bc'], 2), (g.V['c'], 3),
            (g.E['cb'], 4), (g.V['b'], 5),
            (g.E['bb'], 6), (g.V['b'], 7),
            (g.E['bc'], 8), (g.V['c'], 9),
        ]
        if plan != l:
            for i in range(min(len(plan), len(l))):
                print (i, "=!"[plan[i] != l[i]], plan[i], l[i])

        self.assertEqual(plan, l)

        calls = [
            ('choice', [g.E['ab']]),
            ('uniform', 0.0, 1.0),
            ('choice', [g.E['cb'], g.E['cc']]),
            ('uniform', 0.0, 1.0),
            ('uniform', 0.0, 1.0),
            ('choice', [g.E['cb'], g.E['cc']]),
        ]

        if r.calls != calls:
            for i in range(min(len(r.calls), len(calls))):
                print (i, "=!"[r.calls[i] != calls[i]], r.calls[i], calls[i])

        self.assertEqual(p.rng.calls, calls)


class timeout(object):
    @staticmethod
    def alrm(sig, frame):
        assert False, "Timeout"

    def __init__(self, t=1):
        self.t = t

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.alrm)
        signal.alarm(self.t)

    def __exit__(self, t, v, tb):
        signal.alarm(0)


class TestEuler(unittest.TestCase):
    def test_ctor_smoke(self):
        self.assert_(planning.Euler())

    def test_fail_non_euler_a(self):
        p = planning.Euler()
        g = build_graph('ab bc bd')
        p.forced_plan = lambda *al: None
        try:
            p(g, EhmNo(), 'a', '<context>')
        except AssertionError as e:
            self.assertEqual(e.args, ("Graph is not Eulerian",))
        else:
            self.assert_(False, "Expected exception")

    def test_fail_non_euler_b(self):
        p = planning.Euler()
        g = build_graph('ab ba de ed')
        p.forced_plan = lambda *al: None
        try:
            p(g, EhmNo(), 'a', '<context>')
        except AssertionError as e:
            self.assertEqual(e.args, ("Graph is not connected",))
        else:
            self.assert_(False, "Expected exception")

    def test_early_stop(self):
        class Some(EhmNo):
            stops = [0, 0, 0, 1]
            __nonzero__ = lambda s: s.stops.pop(0)
        g = build_graph('ab bc cd de ef fg gh ha')
        p = planning.Euler()
        p.forced_plan = lambda *al: None
        plan = p(g, Some(), 'a', '<context>')
        self.assertEqual([x[0] for x in plan], ['ab', 'b', 'bc'])

    def test_completes(self):
        g = build_graph('ab bc cb ba')
        p = planning.Euler()
        p.forced_plan = lambda *al: None
        with timeout(1):
            p(g, EhmNo(), 'a', '<context>')


class TestGoto(unittest.TestCase):
    def test_ctor_smoke(self):
        self.assert_(planning.Goto())

    def test_shortest(self):
        g = build_graph('ab ac ad bc dc')
        d = {('a', 'b'): (1, 'b'), ('a', 'c'): (1, 'c'), ('a', 'd'): (1, 'd'),
             ('b', 'c'): (1, 'c'), ('d', 'c'): (1, 'c')}
        g.all_pairs_shortest_path = lambda *al: d
        g.is_stuck = lambda *al: False
        p = planning.Goto('c')
        plan = p(g, EhmNo(), 'a', '<context>')
        self.assertEqual([x[0] for x in plan], ['ac', 'c'])

    def test_each_in_turn(self):
        g = build_graph('ab bc cd da')
        d = {
            ('a', 'b'): (1, 'b'),
            ('a', 'c'): (2, 'bc'),
            ('a', 'd'): (3, 'bcd'),
            ('b', 'c'): (1, 'c'),
            ('b', 'd'): (2, 'cd'),
            ('b', 'a'): (3, 'cda'),
            ('c', 'd'): (1, 'd'),
            ('c', 'a'): (2, 'da'),
            ('c', 'b'): (3, 'dab'),
            ('d', 'a'): (1, 'a'),
            ('d', 'b'): (2, 'ab'),
            ('d', 'c'): (3, 'abc'),
        }
        g.all_pairs_shortest_path = lambda *al: d
        g.is_stuck = lambda *al: False
        p = planning.Goto(*'dcba')
        plan = p(g, EhmNo(), 'a', '<context>')
        self.assertEqual(
            '-'.join(x[0] for x in plan),
            'ab-b-bc-c-cd-d-da-a-ab-b-bc-c-cd-d-da-a-ab-b-bc-c-cd-d-da-a')
        #  a ->         d ->             c ->           b ->           a


class TestInteractive(unittest.TestCase):
    def test_ctor_smoke(self):
        self.assert_(planning.Interactive())

    def build(self, result='9\n'):
        pi = planning.Interactive()
        pi.out = cStringIO.StringIO()

        if isinstance(result, BaseException):
            def raiser():
                raise result
            pi.raw_input = raiser
        else:
            pi.raw_input = result if callable(result) else (lambda: result)

        return pi

    def test_choose_choice(self):
        pi = self.build('9\n')
        self.assertEqual(pi.choose(pi, 'abc'), '9\n')

    def test_choose_alts(self):
        pi = self.build()
        alts = ['fleb', 'mefl', 'blof']
        pi.choose(pi, alts)
        out = pi.out.getvalue()
        self.assert_(all(item in out for item in alts),
                     'All items should be listed before prompt')

    def test_choose_sigint(self):
        pi = self.build(KeyboardInterrupt())
        self.assertEqual(pi.choose(pi, 'abc'), None)

    def test_choose_eof(self):
        pi = self.build(EOFError())
        self.assertEqual(pi.choose(pi, 'abc'), None)

    def test_choose_other_exception(self):
        l = [5, 1, 0, 0]
        pi = self.build(lambda: 1 / l.pop() and '0\n')
        self.assertEqual(pi.choose(pi, 'abc'), '0\n')
        self.assertEqual(l, [5])
        self.assert_('huh?' in pi.out.getvalue())


class TestMasterPlan(unittest.TestCase):
    def test_ctor_smoke(self):
        self.assert_(planning.MasterPlan([]))
        self.assert_(planning.MasterPlan(['meffel']))

    def test_inner(self):
        calls = []
        inner = lambda *al: calls.append(al) or ['step']
        p = planning.MasterPlan([inner])
        steps = list(p('<g>', '<h>', '<start>', '<ctx>'))
        self.assertEqual(steps, ['step'])
        self.assertEqual(calls, [('<g>', '<h>', '<start>', '<ctx>')])

    def test_inners(self):
        calls = []
        abe = lambda *al: calls.append(('a', al)) or ['step_a']
        ben = lambda *al: calls.append(('b', al)) or ['step_b']
        p = planning.MasterPlan([abe, ben])
        steps = list(p('<g>', '<h>', '<start>', '<ctx>'))
        self.assertEqual(steps, ['step_a', 'step_b'])
        self.assertEqual(calls, [('a', ('<g>', '<h>', '<start>', '<ctx>')),
                                 ('b', ('<g>', '<h>', 's', '<ctx>'))])
