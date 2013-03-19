# -*- coding: utf-8 -*-
# Copyright (c) 2013 Spotify AB


def deserialize(d, **kw):
    vert_section, edge_section = d.split('\n#\n', 1)

    verts = [line.split(None, 1) for line in vert_section.split('\n') if line]

    edges = [('e%d' % i, e[2], e[0], e[1]) for i, e in
             enumerate([line.split(None, 2)
                        for line in edge_section.split('\n') if line])]

    return verts, edges
