# -*- coding: utf-8 -*-
# Copyright (c) 2013 Spotify AB
import os
import sys
import logging

from graphwalker import codeloader
from graphwalker import tapping

log = logging.getLogger(__name__)


class ReportingPlugin(object):
    """Common (optional) base or example for Graphwalker reporting plugins."""

    def __init__(self, **kw):
        self.context = kw

    def update(self, context):
        self.context.update(context)

    def start_suite(self, suite_name):
        self.suite_name = suite_name

    def end_suite(self):
        pass

    def initiate(self, test_name):
        self.test_name = test_name

    def finalize(self, failure=False):
        pass

    def step_begin(self, step):
        pass

    def step_end(self, step, failure=False):
        pass

    def log(self, origin, message):
        pass

    def attach_to_suite(self, name, data):
        pass

    def attach_to_test(self, name, data):
        pass

    def attach_to_step(self, name, data):
        pass


class Print(ReportingPlugin):
    """Print report to [output]; 'stdout', 'stderr' or object with write()."""

    outputs_map = {'stderr': sys.stderr, 'stdout': sys.stdout}

    def initiate(self, test_name):
        super(Print, self).initiate(test_name)
        self.emit('starting %s' % self.test_name)

    def finalize(self, failure=False):
        pf = ['Fail', 'Pass'][not failure]
        self.emit('%sing %s' % (pf, self.test_name))

    def step_begin(self, step):
        self.emit("Begin step '%s'" % step[1])

    def step_end(self, step, failure=False):
        pf = ['Fail', 'Pass'][not failure]
        self.emit("%sed step '%s'" % (pf, step[1]))

    def log(self, origin, message):
        message = message.rstrip('\r\n')
        if message:
            self.emit('[' + origin + ']' + message)

    def attach_to_suite(self, name, data):
        self.emit("attachment: %r" % name)

    attach_to_test = attach_to_suite
    attach_to_step = attach_to_suite

    def emit(self, message):
        out = self.context.get('output', 'stdout')
        out = self.outputs_map.get(out, out)
        print >>out, message
        out.flush()


class Log(Print):
    """Log report to (name or object) [logger], at [level]."""

    getLogger = staticmethod(logging.getLogger)
    levels = dict(
        (n, getattr(logging, n))
        for n in 'FATAL CRITICAL ERROR WARNING WARN INFO DEBUG'.split())

    @property
    def logger(self):
        logger = self.context.get('logger', log)
        if not callable(getattr(logger, 'log', None)):
            logger = self.getLogger(logger)
        return logger

    @property
    def level(self):
        level = str(self.context.get('level', logging.INFO))
        level = int(level) if level.isdigit() else self.levels[level]
        return level

    def log(self, origin, message):
        if origin != self.logger.name:
            self.emit(message)

    def emit(self, message, *al, **kw):
        self.logger.log(self.level, message % al)


class PathRecorder(ReportingPlugin):
    """Report steps to a file at [path]/[name], saving attachments by name."""

    file = file

    def __init__(self, **kw):
        super(PathRecorder, self).__init__(**kw)
        self.steps = ''

    def initiate(self, test_name):
        super(PathRecorder, self)
        path = self.context.setdefault('path', '.')
        name = self.context.setdefault('name', test_name)
        self.f = self.file(os.path.join(path, name + '.txt'), 'w')

    def step_begin(self, step):
        self.f.write(step[1] + '\n')
        self.steps += step[1] + '\n'

    def finalize(self, failure=False):
        if self.context.get('attach'):
            name = self.context.get('name')
            self.context['reporter'].attach(name + '.txt', self.steps)

        self.f.close()
        del self.f


class Cartographer(ReportingPlugin):
    """Report graph and path steps to a graphviz file and run dot."""

    file = file
    system = os.system
    command = 'dot -T%(imgtype)s -o %(imgfname)s %(dotfname)s'

    def __init__(self, **kw):
        super(Cartographer, self).__init__(**kw)
        self.i = 0
        self.context.setdefault('dotpath', '.')
        self.context.setdefault('imgpath', '.')
        self.context.setdefault('imgtype', 'png')
        self.context.setdefault('attach', False)

    def step_begin(self, step):
        name, self.i = '%s_%04d' % (self.test_name, self.i), self.i + 1
        dotpath = self.context.get('dotpath', '.')
        imgpath = self.context.get('imgpath', '.')
        imgtype = self.context.get('imgtype', 'png')
        dotfname = os.path.join(dotpath, name + '.dot')
        imgfname = os.path.join(imgpath, name + '.' + imgtype)

        self.context['model'].write(dotfname, highlight=(step[0],))
        rc = self.system(
            self.command %
            {'dotfname': dotfname, 'imgfname': imgfname, 'imgtype': imgtype})

        if self.context.get('attach') and not rc:
            r = self.context['reporter']
            with self.file(imgfname) as f:
                r.attach_to_step(dotfname, f.read())


class Attachments(ReportingPlugin):
    """Save attachments to [path]/name."""

    file = file

    def attach_to_suite(self, name, data):
        path = self.context.get('path')
        path = path if path is not None else '.'
        with self.file(os.path.join(path, name), 'w') as f:
            f.write(data)

    attach_to_test = attach_to_suite
    attach_to_step = attach_to_suite


class ReporterHerd(object):
    def each(name):
        def new(self, *al, **kw):
            for r in self.reporters:
                getattr(r, name)(*al, **kw)

        new.__name__ = name
        return new

    def __init__(self, reporters=None, taps=None):
        self.reporters = reporters
        self.taps = taps if taps is not None else [
            tapping.LogTap(self),
            tapping.StreamTap(self, 'sys.stdout'),
            tapping.StreamTap(self, 'sys.stderr')]

    def initiate(self, test_name):
        for tap in self.taps:
            tap.install()

        for r in self.reporters:
            r.initiate(test_name)

    def finalize(self, failure):
        for r in self.reporters:
            r.finalize(failure)

        for tap in self.taps:
            tap.remove()

    update = each('update')
    start_suite = each('start_suite')
    end_suite = each('end_suite')
    step_begin = each('step_begin')
    step_end = each('step_end')
    log = each('log')
    attach_to_suite = each('attach_to_suite')
    attach_to_step = each('attach_to_step')
    attach_to_test = each('attach_to_test')


def build(specs):
    """Import, construct and aggregate requested reporters."""
    reporters = []

    for spec in specs:
        reporters.append(
            codeloader.construct(
                spec,
                default_module=__name__,
                call_by_default=True))

    return ReporterHerd(reporters=reporters)


reporters = [cls
             for cls in locals().values()
             if type(cls) is type
             and issubclass(cls, ReportingPlugin)
             and cls is not ReportingPlugin]
