# -*- coding: utf-8 -*-
# Copyright (c) 2013 Spotify AB
import unittest

from graphwalker import txt


class TestTxt(unittest.TestCase):
    def test_words(self):
        verts, edges = txt.deserialize("foo bar baz")

    def test_lines(self):
        verts, edges = txt.deserialize("foo\nbar\nbaz\n")

    def test_verts(self):
        verts, edges = txt.deserialize("foo\nbar\nbaz\n")
        self.assertEqual(verts, [
            ('v0', 'Start'),
            ('v1', 'foo'),
            ('v2', 'bar'),
            ('v3', 'baz')])

    def test_edges(self):
        verts, edges = txt.deserialize("foo\nbar\nbaz\n")
        self.assertEqual(edges, [
            ('e0', None, 'v0', 'v1'),
            ('e1', None, 'v1', 'v2'),
            ('e2', None, 'v2', 'v3')])

    def test_flash(self):
        verts, edges = txt.deserialize("foo\nbar # kef\nbaz\n")
        vl = [v[1] for v in verts]
        self.assertTrue('bar' in vl)
        self.assertTrue('#' not in vl)
        self.assertTrue('kef' not in vl)
        self.assertTrue('baz' in vl)

    def test_double_slash(self):
        verts, edges = txt.deserialize("foo\nbar // kef\nbaz\n")
        vl = [v[1] for v in verts]
        self.assertTrue('bar' in vl)
        self.assertTrue('//' not in vl)
        self.assertTrue('kef' not in vl)
        self.assertTrue('baz' in vl)

    def test_comment(self):
        verts, edges = txt.deserialize("foo\nbar /* kef keble */ baz\n")
        vl = [v[1] for v in verts]
        self.assertTrue('bar' in vl)
        self.assertTrue('/*' not in vl)
        self.assertTrue('*/' not in vl)
        self.assertTrue('kef' not in vl)
        self.assertTrue('baz' in vl)

    def test_comment_multiline(self):
        verts, edges = txt.deserialize("foo\nbar /* kef\nkeble */ baz\n")
        vl = [v[1] for v in verts]
        self.assertTrue('bar' in vl)
        self.assertTrue('/*' not in vl)
        self.assertTrue('*/' not in vl)
        self.assertTrue('kef' not in vl)
        self.assertTrue('baz' in vl)
