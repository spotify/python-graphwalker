# -*- coding: utf-8 -*-
# Copyright (c) 2013 Spotify AB
import logging
import StringIO
import unittest

from graphwalker import reporting


class TestReporter(unittest.TestCase):
    def build(self):
        return reporting.ReportingPlugin()

    def test_ctor_smoke(self):
        self.assert_(self.build())

    @staticmethod
    def exercise_pass(r1):
        r1.update({'k': 'v'})
        r1.start_suite('suite_name')
        r1.initiate('test_name')
        r1.step_begin(('id0', 'name0'))
        r1.log('test', 'message')
        r1.attach_to_step('hello.txt', 'Hello, world!\n')
        r1.step_end(('id0', 'name0'), False)
        r1.step_begin(('id1', 'name1'))
        r1.step_end(('id1', 'name1'), False)
        r1.attach_to_test('woo.txt', 'Yay!\n')
        r1.finalize(False)
        r1.attach_to_suite('wee.txt', 'Weee!\n')
        r1.end_suite()
        return r1

    @staticmethod
    def exercise_fail(r2):
        fail = AssertionError('exception arg')
        r2.start_suite('suite_name')
        r2.initiate('test_name1')
        r2.step_begin(('id2', 'name2'))
        r2.step_end(('id2', 'name2'), fail)
        r2.finalize(fail)
        r2.end_suite()
        return r2

    def test_api(self):
        r1 = self.exercise_pass(self.build())
        r2 = self.exercise_fail(self.build())
        return r1, r2


class TestPrint(TestReporter):
    def build(self):
        return reporting.Print(output=StringIO.StringIO())

    def test_output(self):
        r1, r2 = self.test_api()
        o1 = r1.context.get('output').getvalue()
        for s in 'test_name name0 message hello.txt'.split():
            self.assertTrue(s in o1)

        o2 = r2.context.get('output').getvalue()
        for s in 'test_name1 name2'.split():
            self.assertTrue(s in o2)

    def test_outmap(self):
        r = reporting.Print()
        r.outputs_map = dict(reporting.Print.outputs_map)
        r.outputs_map['cthulhu'] = c = StringIO.StringIO()
        r.context['output'] = 'cthulhu'
        r.emit('floob!')
        self.assertTrue(c.getvalue())

    def test_writable(self):
        writes = []

        class writable:
            def write(self, out):
                writes.append(out)

            def flush(self):
                pass

        self.exercise_pass(reporting.Print(output=writable()))
        self.assertTrue(writes)


class TestLogger(TestPrint):
    class logger:
        def __init__(self, name='teh_logger'):
            self.calls, self.name = [], name

        def log(self, level, message):
            self.calls.append((level, message))

        def getvalue(self):
            return '\n'.join(m for l, m in self.calls)

    def build(self):
        l = self.logger()
        return reporting.Log(logger=l, output=l)

    def test_log_levels(self):
        r1, r2 = self.test_api()
        l = r1.context['logger']
        self.assertEqual(set(lvl for lvl, m in l.calls), set((logging.INFO,)))

    def test_get_logger(self):
        x, r = {}, reporting.Log(logger='cat')
        r.getLogger = lambda n: x.setdefault(n, self.logger(n))
        self.exercise_pass(r)
        ((name, l),) = x.items()
        self.assertEqual(name, 'cat')
        self.assertEqual(l.name, 'cat')
        self.assertTrue(l.calls)

    def test_avoid_loop(self):
        x, r = {}, reporting.Log(logger='cat')
        r.getLogger = lambda n: x.setdefault(n, self.logger(n))
        r.log('cat', 'cthulhu cats the dog')
        ((name, l),) = x.items()
        self.assertEqual(l.calls, [])


class TestPathRecorder(TestReporter):
    def build(self):
        r = reporting.PathRecorder()
        o = StringIO.StringIO()
        r.file = lambda name, mode: r.context.setdefault('output', o)
        o.close = lambda: r.context.setdefault('closed', True)
        return r

    def test_output(self):
        r1, r2 = self.test_api()

        o1 = r1.context.get('output').getvalue()
        self.assertEqual(o1, 'name0\nname1\n')
        self.assertEqual(r1.context.get('closed'), True)

        o2 = r2.context.get('output').getvalue()
        self.assertEqual(o2, 'name2\n')
        self.assertEqual(r2.context.get('closed'), True)


class TestCartographer(TestReporter):
    def build(self):
        m = []

        class model:
            def write(self, fn, highlight):
                m.append((fn, highlight))

        r = reporting.Cartographer()
        r.context['system_calls'] = []
        r.system = lambda c: r.context['system_calls'].append(c)
        r.context['model_writes'] = m
        r.context['model'] = model()
        return r

    def test_output(self):
        r1 = self.exercise_pass(self.build())

        self.assertEqual(
            r1.context['system_calls'],
            ['dot -Tpng -o ./test_name_0000.png ./test_name_0000.dot',
             'dot -Tpng -o ./test_name_0001.png ./test_name_0001.dot'])
        self.assertEqual(
            r1.context['model_writes'],
            [('./test_name_0000.dot', ('id0',)),
             ('./test_name_0001.dot', ('id1',))])


class TestAttachments(TestReporter):
    def build(self, path=None):
        class f(object):
            def __init__(self):
                self.files = []

            def __call__(self, name, mode):
                self.files.append([name, mode, ''])
                return self

            def write(self, data):
                self.files[-1][-1] += data

            def __enter__(self):
                return self

            def __exit__(self, t, v, tb):
                pass

        r = reporting.Attachments(path=path)
        r.file = r.context['files'] = f()
        return r

    def test_output(self):
        r1 = self.exercise_pass(self.build())
        fs = r1.context['files'].files

        self.assertEqual(fs,
                         [['./hello.txt', 'w', 'Hello, world!\n'],
                          ['./woo.txt', 'w', 'Yay!\n'],
                          ['./wee.txt', 'w', 'Weee!\n']])

    def test_output_path(self):
        r1 = self.exercise_pass(self.build(path='/flebl'))
        fs = r1.context['files'].files
        self.assertEqual(fs[0][0], '/flebl/hello.txt')


class TestReporterHerd(TestReporter):
    def build(self, taps=None):
        r = reporting.ReporterHerd(
            reporters=[
                reporting.ReportingPlugin(),
                reporting.ReportingPlugin(),
                reporting.ReportingPlugin()])
        r.taps = taps or []
        return r

    def test_taps_install_remove(self):
        class mock_tap(object):
            calls = []
            install = lambda s: s.calls.append(('install', s))
            remove = lambda s: s.calls.append(('remove', s))

        m = mock_tap()
        r = self.build([m])
        self.exercise_pass(r)
        self.assertEqual(mock_tap.calls, [('install', m), ('remove', m)])
