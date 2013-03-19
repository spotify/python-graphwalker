# -*- coding: utf-8 -*-
# Copyright (c) 2013 Spotify AB
import re


def deserialize(d, **kw):
    names = re.sub("(?:(?:#|//).*?[\r\n])|/[*](?:.|\n)*?[*]/", " ", d).split()

    if names[:1] != ['Start']:
        names.insert(0, 'Start')

    return (
        [('v%d' % i, v_name)
         for i, v_name in enumerate(names)],
        [('e%d' % i, None, 'v%d' % i, 'v%d' % (i + 1))
         for i in range(len(names) - 1)])
