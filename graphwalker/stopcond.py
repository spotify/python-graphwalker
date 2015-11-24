# -*- coding: utf-8 -*-
# Copyright (c) 2013 Spotify AB
import time

from graphwalker import codeloader


class StopCond(object):
    def start(self, g, context=None):
        self.context = context
        self.seen = set()
        return self

    def __nonzero__(self):
        return False

    def add(self, thing):
        self.seen.add(thing[1])
        return bool(self)

    def progress(self):
        return 'Time passes...'


class Never(StopCond):
    """Never stop."""
    pass


class Seconds(StopCond):
    """Stop after [timeout] (default: 30) seconds."""
    clock = time.time

    def __init__(self, *al, **kw):
        self.timeout = float(al[0] if al else kw.pop('timeout', 30))

    def start(self, g, context=None):
        self.t0 = t = self.clock()
        self.t1 = t + self.timeout
        return self

    def __nonzero__(self):
        return self.clock() >= self.t1

    add = lambda *al, **kw: None

    def progress(self):
        return '%d%%' % (100 * (self.clock() - self.t0) / self.timeout)


class SeenSteps(StopCond):
    """Stop when all given vertices have been visited."""
    def __init__(self, *al, **kw):
        self.targets = set(al)

    def __nonzero__(self):
        return self.targets.issubset(self.seen)

    def progress(self):
        return '%d/%d' % (len(self.seen.intersection(self.targets)),
                          len(self.targets))


class CountSteps(StopCond):
    """Stop after [steps] steps."""
    def __init__(self, *al, **kw):
        self.i, self.n = 0, int(al[0]) if al else kw.get('steps', 100)

    def __nonzero__(self):
        return self.i >= self.n

    def add(self, thing):
        self.i += 1
        return bool(self)


class Coverage(StopCond):
    """Stop after [vertices] or [edges] number of vertices/edges visited."""
    def __init__(self, *al, **kw):
        kw['verts'] = kw.pop('vertices', kw.get('verts', 0))
        self.edge_cov = min(1.0, float(kw.get('edges', 0)) / 100.0)
        self.vert_cov = min(1.0, float(kw.get('verts', 0)) / 100.0)

        if self.edge_cov == 0.0 and self.vert_cov == 0.0:
            self.edge_cov = 1.0

    def start(self, g, context=None):
        self.g = g

        self.edges_seen = set()
        self.edges_count = float(len(g.E.keys()))

        self.verts_seen = set()
        self.verts_count = float(len(g.V.keys()))
        return self

    def __nonzero__(self):
        return (
            len(self.edges_seen) / self.edges_count >= self.edge_cov and
            len(self.verts_seen) / self.verts_count >= self.vert_cov)

    def progress(self):
        x, y = 0, 0

        if self.edge_cov > 0:
            x, y = x + len(self.edges_seen), y + self.edges_count
        if self.vert_cov > 0:
            x, y = x + len(self.verts_seen), y + self.verts_count

        assert y > 0
        return "%d/%d: %d" % (x, y, 100.0 * x / y)

    def add(self, thing):
        x_id = thing[0]
        if x_id in self.g.V:
            self.verts_seen.add(x_id)
        elif x_id in self.g.E:
            self.edges_seen.add(x_id)

        return bool(self)


def build(spec):
    return codeloader.construct(
        spec,
        default_module=__name__,
        call_by_default=True)


conditions = [cls
              for cls in locals().values()
              if type(cls) is type
              and issubclass(cls, StopCond)
              and cls.__doc__
              and cls is not StopCond]
