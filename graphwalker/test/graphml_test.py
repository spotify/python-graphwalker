# -*- coding: utf-8 -*-
# Copyright (c) 2013 Spotify AB
import os
import unittest

from graphwalker import graphml


class TestGraphml(unittest.TestCase):
    here = lambda s, n: os.path.join(os.path.dirname(__file__), n)

    def test_example_abz(self):
        with file(self.here('examples/abz.graphml')) as f:
            verts, edges = graphml.deserialize(f.read())

        self.assertEqual(
            sorted(verts),
            [('n0', 'Start'),
             ('n1', 'v_a'),
             ('n2', 'v_b'),
             ('n3', 'v_c')])

        self.assertEqual(
            sorted(edges),
            [('e0', 'e_zero', 'n0', 'n1'),
             ('e1', 'e_one', 'n1', 'n2'),
             ('e2', 'e_two', 'n2', 'n3')])

    def test_example_odd(self):
        with file(self.here('examples/odd.graphml')) as f:
            verts, edges = graphml.deserialize(f.read())

        self.assertEqual(
            sorted(verts),
            [('n0', 'Start'), ('n1', 'v_a'), ('n2', 'v_b'),
             ('n3', 'v_c'), ('n4', 'v_d'), ('n5', 'v_e')])

        self.assertEqual(
            sorted(edges),
            [('e0', 'e_once', 'n0', 'n1'),
             ('e1', 'e_eb', 'n1', 'n2'),
             ('e2', 'e_ac', 'n1', 'n3'),
             ('e3', 'e_bd', 'n2', 'n4'),
             ('e4', 'e_cd', 'n3', 'n4'),
             ('e5', 'e_de', 'n4', 'n5'),
             ('e6', 'e_ea', 'n5', 'n1')])
