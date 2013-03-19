# -*- coding: utf-8 -*-
# Copyright (c) 2013 Spotify AB
from collections import namedtuple

COST, PATH = 0, 1
inf = 2 ** 31  # approximation of infinity(tm)

VertBase = namedtuple('Vert', 'id name outgoing incoming extra')
EdgeBase = namedtuple('Edge', 'id name src tgt extra')


def parse_name(name, extra=None):
    if name is not None and '\n' in name:
        lines = name.split('\n')
        name = lines.pop(0)
        extra = extra if extra is not None else {}

        for line in lines:
            if '=' in line:
                k, v = line.split('=')
                extra[k.strip()] = v.strip()
            else:
                extra[line.strip()] = True

    return name, extra


class Edge(EdgeBase):
    def __new__(cls, id, name, src, tgt, extra=None):
        name, extra = parse_name(name, extra)
        return tuple.__new__(cls, (id, name, src, tgt, extra))

    def __str__(self):
        return 'e(%s/%s %s->%s)' % self[:4]

    def __getattr__(self, key):
        return self.extra.get(key) if self.extra else None

    def clone(self, new_id):
        return Edge(new_id, self.name, self.src, self.tgt)


class Vert(VertBase):
    def __new__(cls, id, name, outgoing, incoming, extra=None):
        name, extra = parse_name(name, extra)
        outs, ins = tuple(outgoing), tuple(incoming)

        if not all(isinstance(e, Edge) for e in outs + ins):
            raise TypeError("Only edges permitted in edge lists")

        return tuple.__new__(cls, (id, name, outs, ins, extra))

    def __str__(self):
        return 'v(%s/%s)' % (self[0], self[1])

    def __getattr__(self, key):
        return self.extra.get(key) if self.extra else None

    def without_edge_by_id(self, e_id):
        return Vert(self.id, self.name,
                    [e for e in self.outgoing if e.id != e_id],
                    [e for e in self.incoming if e.id != e_id],
                    self.extra)


class Graph(object):
    vert_cls, edge_cls = Vert, Edge
    sentinel = []

    def __init__(self, V=None, E=None, d=None):
        self.V = (V if V is not None else {})
        self.E = (E if E is not None else {})
        self.d = d

    def sanity_check(self):
        for e_id, edge in self.E.items():
            assert isinstance(edge, Edge)
            assert edge.src in self.V
            assert edge.tgt in self.V
            assert edge in self.V[edge.src].outgoing
            assert edge in self.V[edge.tgt].incoming

        for v_id, vert in self.V.items():
            assert isinstance(vert, Vert)
            for edge in vert.outgoing + vert.incoming:
                assert edge is self.E.get(edge.id)

        return True

    def copy(self):
        return Graph(dict(self.V), dict(self.E), self.d)

    def changed(self):
        self.d = None

    def new_edge_id(self):
        for i in xrange(getattr(self, '_edge_id', 0), inf):
            new_id = 'e%d' % i
            if new_id not in self.E and new_id not in self.V:
                self._edge_id = i
                return new_id

    def new_vert_id(self):
        for i in xrange(getattr(self, '_vert_id', 0), inf):
            new_id = 'v%d' % i
            if new_id not in self.E and new_id not in self.V:
                self._vert_id = i
                return new_id

    def replace_vert(self, vert):
        self.V[vert.id] = vert
        self.changed()

    def add_vert(self, id, name=None):
        self.V[id] = vert = Vert(id, name if name is not None else id, (), ())
        self.changed()

        return vert

    def add_edge(self, src, tgt, e_id=None, e_name=sentinel):
        e_id = e_id if e_id is not None else self.new_edge_id()
        e_name = e_name if e_name is self.sentinel else e_name

        self.E[e_id] = edge = Edge(e_id, e_name, src.id, tgt.id)
        self.replace_vert(src._replace(outgoing=src.outgoing + (edge,)))
        self.replace_vert(tgt._replace(incoming=tgt.incoming + (edge,)))
        self.changed()

        return edge

    def del_edge(self, edge):
        self.replace_vert(self.V[edge.src].without_edge_by_id(edge.id))
        self.replace_vert(self.V[edge.tgt].without_edge_by_id(edge.id))
        del self.E[edge.id]
        self.changed()

    def del_vert(self, vert):
        v_id = vert.id

        for e_id, edge in self.E.items():
            if v_id == edge.src or v_id == edge.tgt:
                self.del_edge(edge)

        del self.V[v_id]
        self.changed()

    def copy_edge(self, edge):
        new = edge.clone(self.new_edge_id())
        src, tgt = self.V[edge.src], self.V[edge.tgt]

        self.replace_vert(src._replace(outgoing=src.outgoing + (new,)))
        self.replace_vert(tgt._replace(incoming=tgt.incoming + (new,)))
        self.E[new.id] = new

        return edge

    def vert_degrees(self):
        return (
            dict((v.id, len(v.incoming)) for v in self.V.values()),
            dict((v.id, len(v.outgoing)) for v in self.V.values()))

    def odd_verts(self):
        I, O = self.vert_degrees()

        # innie =def= more incoming than outgoing edges.
        # outie =def= more outgoing than incoming edges.
        innies = sum([[v] * (I[v] - O[v]) for v in I if I[v] > O[v]], [])
        outies = sum([[v] * (O[v] - I[v]) for v in I if O[v] > I[v]], [])

        return innies, outies

    def all_pairs_shortest_path(self):
        d = getattr(self, 'd', None)
        if d:
            return d

        vert_ids = self.V.keys()
        dist = {}

        for i in vert_ids:
            for j in vert_ids:
                if i == j:
                    dist[(i, j)] = (0, ())
                else:
                    for e in self.V[i].outgoing:
                        if e.tgt == j:
                            dist[(i, j)] = (1, (j,))
                            break
                    else:
                        dist[(i, j)] = (inf, None)

        for k in vert_ids:
            for i in vert_ids:
                for j in vert_ids:
                    alt_cost = dist[(i, k)][COST] + dist[(k, j)][COST]
                    cost = dist[(i, j)][COST]
                    if cost > alt_cost:
                        alt_path = dist[(i, k)][PATH] + dist[(k, j)][PATH]
                        dist[(i, j)] = (alt_cost, alt_path)

        self.d = dist
        return dist

    def is_stuck(self, vert):
        d = self.all_pairs_shortest_path()
        for (fm, to), (cost, path) in d.items():
            if fm == vert.id and to != vert.id and cost < inf:
                return False

        return True

    def duplicate_edge_by_ids(self, fm, to):
        for e in self.V[fm].outgoing:
            if e.tgt == to:
                self.copy_edge(e)
                break
        else:
            raise RuntimeError("Attempt to duplicate non-existing edge")

    def eulerize(self):
        innies, outies = self.odd_verts()

        if len(innies) == 0:
            return

        # http://www.geocities.com/model_based_testing/model-based.htm
        # 1. find minimum pairing of innies and outies.
        # 2. lay down extra paths using path info in dists
        # 3. new graph is now g'teed eulerian

        self.dist = d = self.all_pairs_shortest_path()

        tries = sorted((cost, fm, to, path)
                       for (fm, to), (cost, path) in d.items()
                       if cost < inf and fm in innies and to in outies)

        while len(innies):
            for cost, fm, to, path in tries:
                if fm in innies and to in outies:
                    outies.remove(to)
                    innies.remove(fm)
                    a = fm
                    for b in path:
                        self.duplicate_edge_by_ids(a, b)
                        a = b
                    break
            else:
                assert False, "Graph has sinks and cannot be made eulerian"

    file = file

    @staticmethod
    def get_codec(name):
        suffix = name.rsplit('.', 1)[-1]
        return getattr(__import__('graphwalker.' + suffix), suffix)

    @classmethod
    def build(cls, verts, edges):
        El = [Edge(*e) for e in edges]
        Vl = [Vert(v[0], v[1],
                   [e for e in El if e.src == v[0]],
                   [e for e in El if e.tgt == v[0]])
              for v in verts]

        V = dict((v.id, v) for v in Vl if not v.BLOCKED)
        E = dict((e.id, e) for e in El
                 if (e.tgt in V) and (e.src in V) and not e.BLOCKED)

        return cls(V, E)

    @classmethod
    def read(cls, fn, **kw):
        with cls.file(fn) as f:
            verts, edges = cls.get_codec(fn).deserialize(f.read(), **kw)
            return cls.build(verts, edges)

    def serialize(self, fn, **kw):
        codec = self.get_codec(fn)
        return codec.serialize((self.V, self.E), fn.split('.', 1)[0], **kw)

    def write(self, fn, **kw):
        with self.file(fn, 'w') as f:
            f.write(self.serialize(fn, **kw))
