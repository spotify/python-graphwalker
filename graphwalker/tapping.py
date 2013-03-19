# -*- coding: utf-8 -*-
# Copyright (c) 2013 Spotify AB
import logging

from graphwalker import codeloader


class LogTap(logging.Handler):
    get_root_logger = lambda s: logging.getLogger('')

    def __init__(self, target):
        logging.Handler.__init__(self)
        self.target = target

    def emit(self, record):
        self.target.log(record.name, self.format(record))

    def install(self):
        self.get_root_logger().addHandler(self)

    def remove(self):
        self.get_root_logger().removeHandler(self)


class StreamTap(object):
    obj_lookup = staticmethod(codeloader.load)

    def __init__(self, reporter, attr, obj=None, name=None):
        self.reporter = reporter
        if obj is None:
            path, self.key = attr.rsplit('.', 1)
            self.obj = self.obj_lookup(path)
        else:
            self.obj, self.key = obj, attr

        self.name = name if name is not None else self.key

    def write(self, data):
        self.reporter.log(self.name, data.rstrip('\n'))

    def install(self):
        self.saved = getattr(self.obj, self.key)
        setattr(self.obj, self.key, self)

    def remove(self):
        setattr(self.obj, self.key, self.saved)
