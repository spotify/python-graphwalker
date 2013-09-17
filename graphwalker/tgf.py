# -*- coding: utf-8 -*-
# Copyright (c) 2013 Spotify AB


def deserialize(d, **kw):
    vert_section, edge_section = d.split('\n#\n', 1)

    verts = [line.split(None, 1) for line in vert_section.split('\n') if line]

    counts = {}
    edges = []
    for line in edge_section.split('\n'):
        if line:
            fm, to, label = (line.split(None, 2) + [''])[:3]
            c = counts.get(label, 0)
            counts[label] = c + 1
            id = "%s-%d" % (label, c) if c else label
            edges.append((id, label, fm, to))

    return verts, edges
