# -*- coding: utf-8 -*-
# Copyright (c) 2013 Spotify AB
import logging

log = logging.getLogger(__name__)


class Talker(object):
    def __getattr__(self, k):
        def f(*al, **kw):
            print '\033[32m%s\033[0m' % k
            assert k != 'fail', 'Fail because we were asked to'
        f.__name__ = k
        return f


class Logger(object):
    def __getattr__(self, k):
        def f(*al, **kw):
            log.info("%s(*%r, **%r)" % (k, al, kw))
            assert k != 'fail', 'Fail because we were asked to'
        f.__name__ = k
        return f


class Mute(object):
    def __getattr__(self, k):
        return lambda *al, **kw: None
