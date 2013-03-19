# -*- coding: utf-8 -*-
# Copyright (c) 2013 Spotify AB
import unittest

from graphwalker import graph

gg, vv, ee = graph.Graph, graph.Vert, graph.Edge


class TestEdge(unittest.TestCase):
    def test_ctor_smoke(self):
        self.assertTrue(type(ee('id', 'name', 'src', 'tgt')) is ee)

    def test_str(self):
        s = str(ee('id', 'name', 'src', 'tgt'))
        self.assertTrue(type(s) is str)
        self.assertTrue('id' in s)
        self.assertTrue('name' in s)

    def test_tupleness(self):
        assert isinstance(ee('id', 'name', 'src', 'tgt'), tuple)

    def test_clone(self):
        e = ee('id', 'name', 'src', 'tgt')
        c = e.clone('new')
        self.assertEqual(c.id, 'new')
        self.assertEqual(e[1:], c[1:])


class TestVert(unittest.TestCase):
    def test_ctor_smoke(self):
        self.assertTrue(type(vv('id', 'name', (), ())) is vv)

    def test_ctor_fail_len(self):
        self.assertRaises(TypeError, vv, 'id', 'name', 'foo', 'bar', 'baz')

    def test_ctor_fail_non_seq(self):
        self.assertRaises(TypeError, vv, 'id', 'name', 12, 23)

    def test_ctor_fail_non_edge(self):
        self.assertRaises(TypeError, vv, 'id', 'name', ('a',), ('b',))

    def test_str(self):
        s = str(vv('id', 'name', (), ()))
        self.assertTrue(type(s) is str)
        self.assertTrue('id' in s)
        self.assertTrue('name' in s)


g0p = ee('p', 'p', 'a', 'b')
g0a = vv('a', 'a', (g0p,), ())
g0b = vv('b', 'b', (), (g0p,))
g0V, g0E = {'a': g0a, 'b': g0b}, {'p': g0p}


def build_graph(spec):
    g0 = gg()

    for v in sorted(set(spec.replace(' ', ''))):
        g0.add_vert(v)

    for f, t in spec.split():
        g0.add_edge(g0.V[f], g0.V[t])

    return g0


class TestGraph(unittest.TestCase):
    def test_smoke(self):
        assert gg({}, {})

    def test_sanity_empty(self):
        g = gg({}, {})
        assert g.sanity_check()

    def test_sanity_simple(self):
        g = gg(dict(g0V), dict(g0E))
        assert g.sanity_check()

    def test_sanity_fail(self):
        g = gg({}, dict(g0E))
        self.assertRaises(AssertionError, g.sanity_check)

    def test_copy_equal(self):
        g0 = gg(dict(g0V), dict(g0E))
        g1 = g0.copy()
        self.assertEqual(sorted(g0.V.items()), sorted(g1.V.items()))
        self.assertEqual(sorted(g0.E.items()), sorted(g1.E.items()))

    def test_copy_mod(self):
        g0 = gg(dict(g0V), dict(g0E))
        g1 = g0.copy()
        g0.E['q'] = q = ee('q', 'q', 'c', 'd')
        g0.V['c'] = vv('c', 'c', (q,), ())
        g0.V['d'] = vv('d', 'd', (), (q,))
        self.assertNotEqual(sorted(g0.V.items()), sorted(g1.V.items()))
        self.assertNotEqual(sorted(g0.E.items()), sorted(g1.E.items()))
        g0.V.clear()
        self.assertRaises(AssertionError, g0.sanity_check)
        g1.sanity_check()

    def test_new_edge_id(self):
        g0 = gg(dict(g0V), dict(g0E))
        ei = g0.new_edge_id()
        self.assertTrue(ei not in g0.V)
        self.assertTrue(ei not in g0.E)

    def test_new_edge_id_stability(self):
        g0 = gg(dict(g0V), dict(g0E))
        ei = g0.new_edge_id()
        ej = g0.new_edge_id()
        self.assertEqual(ei, ej)

    def test_new_edge_id_change(self):
        g0 = gg(dict(g0V), dict(g0E))
        ei = g0.new_edge_id()
        g0.E[ei] = ee(ei, ei, 'b', 'a')
        ej = g0.new_edge_id()
        self.assertNotEqual(ei, ej)

    def test_new_vert_id(self):
        g0 = gg(dict(g0V), dict(g0E))
        vi = g0.new_vert_id()
        self.assertTrue(vi not in g0.V)
        self.assertTrue(vi not in g0.E)

    def test_new_vert_id_stability(self):
        g0 = gg(dict(g0V), dict(g0E))
        vi = g0.new_vert_id()
        vj = g0.new_vert_id()
        self.assertEqual(vi, vj)

    def test_new_vert_id_change(self):
        g0 = gg(dict(g0V), dict(g0E))
        vi = g0.new_vert_id()
        g0.V[vi] = vv(vi, vi, (), ())
        vj = g0.new_vert_id()
        self.assertNotEqual(vi, vj)

    def test_del_edge(self):
        E = {'p': ee(*'ppab'), 'q': ee(*'qqab'), 'r': ee(*'rrab')}
        V = {'a': vv('a', 'a', (E['p'], E['q'], E['r']), ()),
             'b': vv('b', 'b', (), (E['p'], E['q'], E['r']))}

        g = gg(V, E)
        edge = g.E['q']

        g.del_edge(edge)

        self.assertEqual(g.E, {'p': ee(*'ppab'), 'r': ee(*'rrab')})
        self.assertEqual(g.V, {
            'a': vv('a', 'a', (E['p'], E['r']), ()),
            'b': vv('b', 'b', (), (E['p'], E['r']))})

    def test_del_vert_with_outlink(self):
        g = gg(dict(g0V), dict(g0E))
        vert = g.V['a']
        g.del_vert(vert)
        self.assertEqual(g.V, {'b': vv('b', 'b', (), ())})
        self.assertEqual(g.E, {})

    def test_del_vert_with_inlink(self):
        g = gg(dict(g0V), dict(g0E))
        vert = g.V['b']
        g.del_vert(vert)
        self.assertEqual(g.V, {'a': vv('a', 'a', (), ())})
        self.assertEqual(g.E, {})

    def FIXME_tst_copy_edge(self):
        E = {'p': ee(*'ppab'), 'q': ee(*'qqab')}

        V = {'a': vv('a', 'a', (E['p'], E['q'])),
             'b': vv('b', 'b', ())}

        g = gg(V, E)
        q = g.E['q']
        x0 = g.copy_edge(q)

        self.assertEqual(x0, ee('x0', 'q', 'a', 'b'))

        self.assertEqual(g.E, {'p': ee(*'ppab'), 'q': ee(*'qqab'), 'x0': x0})
        self.assertEqual(g.V, {
            'a': vv('a', 'a', (E['p'], E['q'], E['x0'])),
            'b': vv('b', 'b', ())})

    def test_vert_degrees(self):
        g = gg(dict(g0V), dict(g0E))
        self.assertEqual(
            g.vert_degrees(),
            ({'a': 0, 'b': 1},   # I
             {'a': 1, 'b': 0}))  # O

    def test_odd_verts(self):
        E = {'p': ee(*'ppab'), 'q': ee(*'qqbc')}

        V = {'a': vv('a', 'a', (E['p'],), ()),
             'b': vv('b', 'b', (E['q'],), (E['p'],)),
             'c': vv('c', 'c', (), (E['q'],))}

        g = gg(V, E)
        g.sanity_check()
        self.assertEqual(g.odd_verts(), (['c'], ['a']))

    def test_apsp(self):
        g = gg(dict(g0V), dict(g0E))
        g.d = g.all_pairs_shortest_path()
        self.assertEqual(g.d, {
            ('a', 'a'): (0, ()),
            ('a', 'b'): (1, ('b',)),
            ('b', 'a'): (graph.inf, None),
            ('b', 'b'): (0, ()),
        })

    def test_is_stuck(self):
        g = gg(dict(g0V), dict(g0E))
        g.d = g.all_pairs_shortest_path()
        self.assertFalse(g.is_stuck(g0a))
        self.assertTrue(g.is_stuck(g0b))

    def test_eulerize(self):
        g0 = build_graph('ab ac bd cd de ea')
        self.assertEqual(g0.odd_verts(), (['d'], ['a']))
        g0.eulerize()
        self.assertEqual(g0.odd_verts(), ([], []))


class TestGraphIO(unittest.TestCase):
    class GraphSub(graph.Graph):
        class file(object):
            read_value = '<mefl>'
            _inst = None

            def __init__(self, *al):
                self.__class__._inst = self
                self.al = al
                self.calls = []

            def read(self, size=None):
                self.calls.append(('read', size))
                return self.read_value

            def write(self, data=None):
                self.calls.append(('write', data))

            def __enter__(self):
                self.calls.append(('__enter__'))
                return self

            def __exit__(self, t, v, tb):
                self.calls.append(('__exit__', t, v, tb))

        class Codec(object):
            def __init__(self, name):
                self.calls = [('__init__', name)]
                e0 = ('e_id', 'e_name', 'a_id', 'b_id')
                v0 = ('a_id', 'a_name')
                v1 = ('b_id', 'b_name')
                self.ve = [v0, v1], [e0]

            def deserialize(self, what):
                self.calls.append(('deserialize', what))
                return self.ve

            def serialize(self, VE, name, **kw):
                self.calls.append(('serialize', VE, name, kw))

        @classmethod
        def get_codec(cls, name):
            cls._codec = cls.Codec(name)
            return cls._codec

    def build(self):
        class GraphSubSub(self.GraphSub):
            pass
        gs = GraphSubSub
        gs.file._inst = None
        return gs

    def test_read_smoke(self):
        self.build().read('fleb.mef')

    def test_read_file_ops(self):
        gs = self.build()
        gs.read('fleb.mef')
        self.assertTrue(gs.file._inst, "File opened")
        self.assertEqual(gs.file._inst.al, ("fleb.mef",))
        self.assertEqual(
            gs.file._inst.calls,
            [('__enter__'), ('read', None), ('__exit__', None, None, None)])

    def test_read_codec_ops(self):
        gs = self.build()
        gs.read('fleb.mef')
        self.assertTrue(gs._codec, "Codec created")
        self.assertEqual(
            gs._codec.calls,
            [('__init__', 'fleb.mef'), ('deserialize', '<mefl>')])

    def test_read_result_types(self):
        gs = self.build()
        g = gs.read('fleb.mef')

        self.assertEqual([type(e) for e in g.E.values()], [graph.Edge])
        self.assertEqual([type(v) for v in g.V.values()], [graph.Vert] * 2)

    def test_read_result_keys(self):
        gs = self.build()
        g = gs.read('fleb.mef')

        self.assertEqual(sorted(g.E.keys()), ['e_id'])
        self.assertEqual(sorted(g.V.keys()), ['a_id', 'b_id'])

    def test_read_result_relations(self):
        gs = self.build()
        g = gs.read('fleb.mef')

        a, b, e = g.V['a_id'], g.V['b_id'], g.E['e_id']

        self.assertEqual(g.E.items(), [('e_id', e)])
        self.assertEqual(a.incoming, ())
        self.assertEqual(a.outgoing, (e,))
        self.assertEqual(b.incoming, (e,))
        self.assertEqual(b.outgoing, ())

        self.assertEqual(e.src, a.id)
        self.assertEqual(e.tgt, b.id)

    def test_read_result_blocked_edge(self):
        gs = self.build()
        c = gs.Codec('mef')
        gs.get_codec = staticmethod(lambda *al: c)
        e0 = ('e_id', 'e_name', 'a_id', 'b_id')
        e1 = ('x_id', 'x_name\nBLOCKED', 'b_id', 'a_id')
        v0 = ('a_id', 'a_name')
        v1 = ('b_id', 'b_name')
        c.ve = [v0, v1], [e0, e1]
        g = gs.read('fleb.mef')

        self.assertEqual(sorted(g.E.keys()), ['e_id'])
        self.assertEqual(sorted(g.V.keys()), ['a_id', 'b_id'])

    def test_read_result_blocked_vert(self):
        gs = self.build()
        c = gs.Codec('mef')
        gs.get_codec = staticmethod(lambda *al: c)
        e0 = ('e_id', 'e_name', 'a_id', 'b_id')
        e1 = ('x_id', 'x_name', 'b_id', 'c_id')
        e2 = ('y_id', 'y_name', 'a_id', 'c_id')
        v0 = ('a_id', 'a_name')
        v1 = ('b_id', 'b_name\nBLOCKED')
        v2 = ('c_id', 'c_name')
        c.ve = [v0, v1, v2], [e0, e1, e2]
        g = gs.read('fleb.mef')

        self.assertEqual(sorted(g.E.keys()), ['y_id'])
        self.assertEqual(sorted(g.V.keys()), ['a_id', 'c_id'])

    def test_read_result_blocked_none(self):
        gs = self.build()
        c = gs.Codec('mef')
        gs.get_codec = staticmethod(lambda *al: c)
        e0 = ('e_id', 'e_name', 'a_id', 'b_id')
        e1 = ('x_id', None, 'b_id', 'c_id')
        e2 = ('y_id', 'y_name', 'a_id', 'c_id')
        v0 = ('a_id', 'a_name')
        v1 = ('b_id', None)
        v2 = ('c_id', 'c_name')
        c.ve = [v0, v1, v2], [e0, e1, e2]
        g = gs.read('fleb.mef')

        self.assertEqual(sorted(g.E.keys()), ['e_id', 'x_id', 'y_id'])
        self.assertEqual(sorted(g.V.keys()), ['a_id', 'b_id', 'c_id'])

    def test_serialize_smoke(self):
        g = self.build()()
        g.serialize('name')

    def test_serialize_calls(self):
        gs = self.build()
        g = gs()

        g.serialize('name', key='val')

        self.assertEqual(
            gs._codec.calls,
            [('__init__', 'name'),
             ('serialize', ({}, {}), 'name', {'key': 'val'})])

    def test_write_serialize(self):
        gs = self.build()
        g = gs()
        serialize_calls = []
        g.serialize = lambda *al, **kw: serialize_calls.append((al, kw))

        g.write('name', key='val')

        self.assertEqual(
            serialize_calls,
            [(('name',), {'key': 'val'})])

    def test_write_write(self):
        gs = self.build()
        g = gs()
        g.serialize = lambda *al, **kw: 'x'

        g.write('name', key='val')

        self.assertEqual(
            gs.file._inst.calls,
            [('__enter__'), ('write', 'x'), ('__exit__', None, None, None)])
