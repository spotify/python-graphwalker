# -*- coding: utf-8 -*-
# Copyright (c) 2013 Spotify AB
import logging

from graphwalker import codeloader

log = logging.getLogger(__name__)


class Executor(object):
    def __init__(self, actor, reporter, debugger=None):
        if isinstance(actor, str):
            actor = codeloader.construct(actor, call_by_default=True)
        self.actor = actor
        self.reporter = reporter
        if isinstance(debugger, str):
            debugger = codeloader.construct(debugger, call_by_default=True)
        self.debugger = debugger
        self.log = log

    def call(self, label, **kw):
        top = label.split('\n', 1)[0]
        name = top.split('[', 1)[0].split('/', 1)[0]

        met = getattr(self.actor, name)
        assert met is not None, "Expected to find method for %r" % name

        met(**kw)

    def run(self, name, plan, context):
        context.update({'actor': self.actor})
        self.plan = plan
        self.context = context
        self.reporter.update(context)
        self.reporter.initiate(name)
        r, e = None, None

        getattr(self.actor, 'setup', lambda ctx: None)(context)

        for item in self.plan:
            if not item[1]:
                continue

            self.reporter.step_begin(item)
            getattr(self.actor, 'step_begin', lambda step: None)(item)

            try:
                self.last = item
                self.call(item[1])
            except Exception, e:
                self.log.exception('failure in %r' % item[1])
                debugger = getattr(self.debugger, 'set_trace', self.debugger)
                if callable(debugger):
                    debugger()

            r = getattr(self.actor, 'step_end', lambda *al: None)(item, e)
            self.reporter.step_end(item, e)

            if r == 'RECOVER':
                e = None
            elif e:
                break

        getattr(self.actor, 'teardown', lambda ctx: None)(context)
        self.reporter.finalize(e)
