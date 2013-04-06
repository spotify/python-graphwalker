# -*- coding: utf-8 -*-
# Copyright (c) 2013 Spotify AB
import logging
import pdb
import random
import sys

from graphwalker import codeloader
from graphwalker import stopcond

# some ghetto enums
COST, PATH = 0, 1

# approximation of infinity(tm)
inf = 2 ** 31
log = logging.getLogger(__name__)


class Planner(object):
    randcls = random.Random

    def __init__(self, *al, **kw):
        self.al, self.kw = al, kw
        self.rng = self.randcls(self.kw.get('seed'))

    def _setup(self, g, stop, start, context):
        for ident, vert in g.V.items():
            if vert.name == start:
                self.vert = vert
                break
        else:
            if start in g.V:
                self.vert = g.V[start]
            else:
                raise RuntimeError("Could not find start vertex")

        stop.add(vert)

        self.g, self.plan, self.stop = g, [], stop

        return self.g.V, self.g.E, self.plan, self.vert

    def forced_plan(self, plan=None):
        """Enter forced steps from Start source vertex.

        The start node is normally a source, but sometimes the source is a
        larger string of single-edge vertices. This enters them into the plan.
        """
        plan = plan if plan is not None else self.plan
        I, O = self.g.vert_degrees()

        while len(self.vert.outgoing) == 1 and I[self.vert.id] == 0:
            self.g.del_vert(self.vert)
            self.vert = self.step(self.vert, self.vert.outgoing[0], plan)
            I, O = self.g.vert_degrees()

    def visit(self, it, plan=None):
        plan = self.plan if plan is None else plan
        self.stop.add(it)
        plan.append(it)

    def step(self, vert, edge, plan=None):
        plan = self.plan if plan is None else plan

        assert edge.src == vert.id, 'Edge not from this vertex'

        dest = self.g.V[edge.tgt]

        self.visit(edge, plan)
        self.visit(dest, plan)
        return dest


class EvenRandom(Planner):
    def __call__(self, g, stop, start, context):
        """Walk through the graph by random edges until done."""
        self._setup(g, stop, start, context)
        return iter(self)

    def choose_edge(self, edges):
            return self.rng.choice(edges)

    def __iter__(self):
        while not self.stop:
            edge = self.choose_edge(self.vert.outgoing)
            self.stop.add(edge)
            yield edge
            self.vert = self.g.V[edge.tgt]
            self.stop.add(self.vert)
            yield self.vert


class Random(EvenRandom):
    def choose_edge(self, edges):
        naive, weighted = [], []
        for e in edges:
            if e.weight is None:
                naive.append(e)
            elif e.weight[-1:] == '%':
                weighted.append((e, float(e.weight[:-1]) / 100))
            else:
                weighted.append((e, float(e.weight)))

        if not weighted:
            return self.rng.choice(edges)

        total_given_probability = sum(w for e, w in weighted)
        remaining = 1.0 - total_given_probability

        if total_given_probability > 1.001:
            log.warn("Probalities supplied exceed unity")

        if len(naive) > 0:
            if remaining <= 0:
                log.warn("Unweighted edges get zero probability")
            else:
                weighted.extend((e, remaining / len(naive)) for e in naive)
        else:
            if remaining >= 0.01:
                log.warn("Weighted edges sum to less than unity")

        x, X = 0, self.rng.uniform(0.0, sum(w for e, w in weighted))
        for e, w in weighted:
            x += w
            if x >= X:
                return e

        return e


class Euler(Planner):
    def __call__(self, g, stop, start, context):
        """Walk through the graph by ordered edges until done."""
        self._setup(g, stop, start, context)

        self.g = self.g.copy()
        self.forced_plan()
        self.g.eulerize()

        self.stop = stopcond.Never().start(g, None)
        vert = self.vert
        seen = set()

        def loop(vert):
            subplan = []
            begin = vert
            while len(seen) < len(self.g.E):
                for edge in vert.outgoing:
                    if edge.id not in seen:
                        seen.add(edge.id)
                        vert = self.step(vert, edge, subplan)
                        break
                else:
                    assert vert.id == begin.id, "Graph is not Eulerian"
                    break

            return subplan

        plan = loop(vert)  # initial plan

        while len(seen) < len(self.g.E):
            j = 0
            for i in range(len(plan)):
                if self.g.V.get(plan[i].id) is not plan[i]:
                    continue

                vert = plan[i]
                for edge in vert.outgoing:
                    if edge.id not in seen:
                        # splice new loop into plan
                        plan[i + 1: i + 1] = loop(vert)
                        j += 1
                        break
            else:
                assert j, "Graph is not connected"

        self.plan, plan = [], self.plan + plan
        for step in plan:
            if stop:
                break
            self.visit(step)

        return self.plan


class Goto(Planner):
    def __init__(self, *al, **kw):
        self.al, self.kw = al, kw
        self.goals = self.al
        self.repeat = kw.pop('repeat', 1)

    def __call__(self, g, stop, start, context):
        self._setup(g, stop, start, context)
        self.d = d = self.g.all_pairs_shortest_path()

        for i in xrange(self.repeat or inf):
            for goal in self.goals:
                if self.g.is_stuck(self.vert) or self.stop:
                    break
                if goal == 'random':
                    goal = self.rng.choice(self.g.V.keys())

                try:
                    cost, path = min(d[(self.vert.id, v.id)]
                                     for v in self.g.V.values()
                                     if ((v.name == goal or
                                          v.id == goal) and
                                         v is not self.vert))
                    plan = path
                except ValueError:
                    continue

                for item in plan:
                    edge = [e for e in self.vert.outgoing
                            if e.tgt == item][0]
                    self.vert = self.step(self.vert, edge)

        return self.plan


class Interactive(Planner):
    """Planner that yields steps (or not) from user interaction.

    The protocol between choose and iterplan is deliberately kept simple to
    keep it simple to replace the choose method.
    """
    raw_input = raw_input
    out = sys.stderr
    debugger = pdb.Pdb('\t', sys.stdin, sys.stderr)

    help = """\
0-n:    Traverse edge
h(elp)  This message
d(ebug) Enter Pdb
g(oto)  Use Goto planner to go some vertex
f(orce) Forcibly insert some words into the plan
j(ump)  Forcibly set the vert where the planner believes it is at
q(uit)  End the interactive session
"""

    def choose(self, planner, alts):
        while True:
            for i in range(len(alts)):
                print >>self.out, i, alts[i]
            try:
                self.out.write('> ')
                return self.raw_input()
            except KeyboardInterrupt:
                return None
            except EOFError:
                return None
            except Exception, e:
                print >>self.out, 'huh? %r' % e

    choose_fn = choose

    def __init__(self, *al, **kw):
        self.al, self.kw = al, kw

    def goto(self, goals):
        stop = stopcond.Never().start(self.g, self.context)
        return Goto(*goals)(self.g, stop, self.vert.id, self.context)

    def choose_vert(self, name):
        if name in self.g.V:
            return self.g.V[name]

        candidates = [v for v in self.g.V.values() if v.name == name]
        if len(candidates) == 1:
            return candidates[0]
        else:
            i = self.choose_fn(self, self.format_vert_list(candidates))
            return candidates[int(i)]

    def __call__(self, g, stop, start, context):
        self._setup(g, stop, start, context)
        self.context = context
        return iter(self)

    def format_vert_list(self, verts):
        V = self.g.V
        alts = []
        for v in verts:
            outs = set(['[%s]\t--(%s)-->%s' % (e.id, e.name, V[e.tgt].name)
                        for e in v.outgoing])
            alts.append(v.name + '\n  ' + '\n  '.join(outs))
        return alts

    def format_edge_list(self, edges):
        V = self.g.V
        return ["[%s]\t%s--(%s)-->%s" %
                (e.id, V[e.src].name, e.name, V[e.tgt].name)
                for e in edges]

    def __iter__(self):
        while True:
            edges = self.vert.outgoing

            if not edges:
                raise StopIteration()

            where = "== Currently at: %s [%s]" % (self.vert.name, self.vert.id)
            print >>self.out, where
            if self.stop:
                print >>self.out, "According to end conditions, we're done"

            i = self.choose_fn(self, self.format_edge_list(edges))
            self.out.flush()

            if i in ('q', None):  # quit
                raise StopIteration()

            elif i == '':
                print >>self.out, 'huh?'
                continue

            elif i[0] == 'd':  # debugger
                self.debugger.set_trace()

            elif i[0] == 'f':  # force
                for s in i.split()[1:]:
                    yield (s, s, ())

            elif i[0] == 'g':  # goto
                for name in i.split()[1:]:
                    for step in self.goto([self.choose_vert(name).id]):
                        yield step
                        self.vert = step

            elif i[0] == 'j':  # jump
                while True:
                    try:
                        self.vert = self.choose_vert(i.split()[-1])
                        break
                    except Exception, e:
                        print >>self.out, 'huh? %r' % e

            elif i[0] in 'h?':
                print >>self.out, self.help

            elif i.strip().isdigit():
                index = int(i.strip())
                if index >= len(edges):
                    print >>self.out, 'huh?'
                else:
                    edge = edges[index]

                    self.vert = self.step(self.vert, edge)
                    yield edge
                    yield self.vert


class MasterPlan(Planner):
    def __init__(self, plans):
        self.plans = plans
        self.i = 0

    def __call__(self, g, stop, start, context):
        self.step = (None, start)
        while self.i < len(self.plans):
            planner = self.plans[self.i]
            start = self.step[0] or self.step[1]
            for step in planner(g, stop, start, context):
                self.step = step
                yield step
            self.i += 1


def build(specs):
    """Import, construct and aggregate requested reporters."""
    planners = []

    for spec in specs:
        planners.append(
            codeloader.construct(
                spec,
                default_module=__name__,
                call_by_default=True))

    if len(planners) == 1:
        return planners[0]
    else:
        return MasterPlan(planners)
