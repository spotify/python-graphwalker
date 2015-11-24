# -*- coding: utf-8 -*-
# Copyright (c) 2013 Spotify AB
"""Parser for GML files.

# http://www.fim.uni-passau.de/fileadmin/files/lehrstuhl/brandenburg/projekte/gml/gml-technical-report.pdf

Grammar:

  GML		::= List
  List		::= (whitespace* Key whitespace+ Value)*
  Value		::= Integer | Real | String | [ List ]
  Key		::= [ a-z A-Z ] [ a-z A-Z 0-9 ]*
  Integer	::= sign digit+
  Real		::= sign digit* . digit* mantissa
  String	::= " instring "
  sign		::= empty | + | -
  digit		::= [0-9]
  Mantissa	::= empty | E sign digit
  instring	::= [^&,"] | & character+ ;
  whitespace	::= space | tabulator | newline

Entity names are not mapped.
"""

import re

token_pattern = '([^ \t\n"]+)|("[^"]*")'
key_pattern = '[A-Za-z][0-9A-Za-z_-]*'


def check_key(s):
    assert re.match(key_pattern, s), 'parse error at %r' % s
    return s


def parse_value(s, ts):
    if s == '[':
        return parse(ts)
    elif (s[0] + s[-1]) == '\"\"':
        return ts, s[1:-1]
    elif '.' in s:
        return ts, float(s)
    else:
        return ts, int(s)


def parse(ts):
    d = []
    while len(ts) > 1 and ts[0] not in ']':
        key = check_key(ts[0])
        ts, val = parse_value(ts[1], ts[2:])
        d.append((key, val))

    return ts[1:], tuple(d)


def build_vert(vl):
    v_id, v_name = None, None

    for key, value in vl:
        if key == 'id':
            v_id = str(value)
        elif key == 'label':
            v_name = value

    assert v_id is not None
    v_name = v_id if v_name is None else v_name

    return (v_id, v_name)


def build_edge(el, serial):
    e_id, e_name, e_src, e_tgt = 'e%d' % serial, None, None, None

    for key, value in el:
        if key == 'label':
            e_name = value
        elif key == 'source':
            e_src = str(value)
        elif key == 'target':
            e_tgt = str(value)

    return (e_id, e_name, e_src, e_tgt)

ID, NAME, EDGES, SRC, TGT = 0, 1, 2, 2, 3


def deserialize(d, **kw):
    commented = re.sub("\n\\s*#[^\n]*", "\n", d)
    tokenized = [mo[0] or mo[1] for mo in re.findall(token_pattern, commented)]
    empty, tree = parse(tokenized)
    serial = iter(xrange(0, 2 ** 62)).next
    verts, edges = [], []

    for key, node in tree:
        if key.lower() == 'graph':
            for key, val in node:
                if key.lower() == 'node':
                    verts.append(build_vert(val))
                elif key.lower() == 'edge':
                    edges.append(build_edge(val, serial()))

            return verts, edges
    else:
        assert False, "Could not find graph in file."
