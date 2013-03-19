# -*- coding: utf-8 -*-
# Copyright (c) 2013 Spotify AB


def parse_spec(spec, default_module):
    """Parse a spec of the form module.class:kw1=val,kw2=val.

    Returns a triple of module, classname, arguments list and keyword dict.
    """
    name, args = (spec.split(':', 1) + [''])[:2]

    if '.' not in name:
        if default_module:
            module, klass = default_module, name
        else:
            module, klass = name, None
    else:
        module, klass = name.rsplit('.', 1)

    al = [a for a in args.split(',') if a and '=' not in a]
    kw = dict(a.split('=', 1) for a in args.split(',') if '=' in a)

    return module, klass, al, kw


def load(module, klass=None):
    if klass:
        return getattr(__import__(module, globals(), locals(), [klass]), klass)
    elif '.' not in module:
        return __import__(module)
    else:
        return getattr(__import__(module), module.rsplit('.', 1)[-1])


def construct(spec, default_module='', call_by_default=False):
    module, klass, al, kw = parse_spec(spec, default_module)
    cls = load(module, klass)
    if callable(cls) and (':' in spec or call_by_default):
        return cls(*al, **kw)
    else:
        return cls
