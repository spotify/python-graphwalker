# -*- coding: utf-8 -*-
# Copyright (c) 2013 Spotify AB
import unittest

from graphwalker import tgf


class TestTGF(unittest.TestCase):
    data0 = """\
n0 Start
n1 v_a
n2 v_b
n3 v_c
#
n0 n1 e_zero
n1 n2 e_one
n2 n3 e_two
"""

    def test_example_abz(self):
        verts, edges = tgf.deserialize(self.data0)

        self.assertEqual(
            sorted(verts),
            [['n0', 'Start'],
             ['n1', 'v_a'],
             ['n2', 'v_b'],
             ['n3', 'v_c']])

        self.assertEqual(
            sorted(edges),
            [('e0', 'e_zero', 'n0', 'n1'),
             ('e1', 'e_one', 'n1', 'n2'),
             ('e2', 'e_two', 'n2', 'n3')])
