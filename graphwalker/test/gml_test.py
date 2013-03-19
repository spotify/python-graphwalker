# -*- coding: utf-8 -*-
# Copyright (c) 2013 Spotify AB
import unittest

from graphwalker import gml


class TestGML(unittest.TestCase):
    data0 = """\
graph [
  directed 1
  node [ id 0 label "Start" ]
  node [ id 1 label "v_a" ]
  node [ id 2 label "v_b" ]
  node [ id 3 label "v_c" ]
  edge [ source 0 target 1 label "e_zero" ]
  edge [ source 1 target 2 label "e_one" ]
  edge [ source 2 target 3 label "e_two" ] ]
"""

    def test_example_abz(self):
        verts, edges = gml.deserialize(self.data0)

        self.assertEqual(
            sorted(verts),
            [('0', 'Start'),
             ('1', 'v_a'),
             ('2', 'v_b'),
             ('3', 'v_c')])

        self.assertEqual(
            sorted(edges),
            [('e0', 'e_zero', '0', '1'),
             ('e1', 'e_one', '1', '2'),
             ('e2', 'e_two', '2', '3')])
