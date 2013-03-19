# -*- coding: utf-8 -*-
# Copyright (c) 2013 Spotify AB
import xml.etree.ElementTree as ET

y = '{http://www.yworks.com/xml/graphml}'
ns = '{http://graphml.graphdrawing.org/xmlns}'
nodestr = './/' + ns + 'node'
edgestr = './/' + ns + 'edge'


def deserialize(d, **kw):
    doc = ET.fromstring(d)
    verts, edges = [], []

    for n in doc.findall('.//' + ns + 'node'):
        l = n.find('.//' + y + 'NodeLabel')
        if l is None:
            continue

        verts.append((n.attrib['id'], l.text.strip()))

    for n in doc.findall('.//' + ns + 'edge'):
        l = n.find('.//' + y + 'EdgeLabel')
        e_id = n.attrib['id']
        e_name = l.text.strip() if l is not None else None
        e_src = n.attrib['source']
        e_tgt = n.attrib['target']
        edges.append((e_id, e_name, e_src, e_tgt))

    return verts, edges
