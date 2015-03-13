# -*- coding: utf-8 -*-
# Copyright (c) 2013 Spotify AB
import dot_parser


def unquote(s):
    return s[1:-1] if s and s[0] == s[-1] and s[0] in "\"\'" else s


def deserialize(d, **kw):

    seqno = (lambda q=iter(xrange(0, 2 ** 31)).next: 'e%d' % q())

    dot = dot_parser.parse_dot_data(d)

    verts = [(unquote(node.get_name()),
              unquote(node.get_label() or node.get_name()))
             for node in dot.get_nodes()
             if node.get_name() not in ('graph', 'node', 'edge')]

    edges = [(seqno(),
              unquote(link.get_label()),
              unquote(link.get_source()),
              unquote(link.get_destination()))
             for link in dot.get_edges()]

    if dot.get_graph_type() == 'graph':
        # add back-edges to be equivalent to undirected graph
        edges.extend([(seqno(), l, t, s) for i, l, s, t in edges])

    return verts, edges


def serialize(VE, name="G", **kw):
    highattr = ',color=red,fontcolor=red,style=filled,fillcolor="#ffeeee"'
    highlight = kw.get('highlight') or []
    V, E = VE[:2]

    s = "digraph \"%s\" {\n" % (name,)

    for v in sorted(V.values()):
        x = highattr if v[0] in highlight else ''
        s += "  \"%s\" [label=\"%s\"%s];\n" % (
            v[0], (v[1] or '').replace('\n', ' '), x)

    s += "\n"

    for e in sorted(E.values()):
        x = highattr if e[0] in highlight else ''
        s += "  \"%s\" -> \"%s\" [label=\"%s\"%s];\n" % (
            e[2], e[3], (e[1] or '').replace('\n', ' '), x)

    s += "}\n"

    return s
