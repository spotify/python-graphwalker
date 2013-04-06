# -*- coding: utf-8 -*-
# Copyright (c) 2013 Spotify AB
import os
import unittest

from graphwalker import planning
from graphwalker import stopcond
from graphwalker import reporting
from graphwalker import executor
from graphwalker import graph


class TestInteraction(unittest.TestCase):
    def setUp(self):
        self._old_pythonpath = os.environ.get('PYTHONPATH', None)
        os.environ['PYTHONPATH'] = '.'

    def tearDown(self):
        old = getattr(self, '_old_pythonpath', None)
        if old is not None:
            os.environ['PYTHONPATH'] = old
        else:
            del os.environ['PYTHONPATH']

    def test_by_interaction(self):
        """Interaction self-test.

        For comparison, try this:

            PYTHONPATH=. python graphwalker/cli.py --reporter=Print \\
              graphwalker/test/examples/selftest.graphml \\
              graphwalker.test.interactor.Interactor
        """
        outer = self

        class HijackReporter(reporting.ReportingPlugin):
            def finalize(self, failure=False):
                outer.assertFalse(failure)

        reporter = HijackReporter()
        plan = planning.build(['Random'])
        stop = stopcond.build('Coverage')
        model = graph.Graph.read('graphwalker/test/examples/selftest.graphml')
        actor = 'graphwalker.test.interactor.Interactor'
        exe = executor.Executor(actor, reporter)

        context = {
            'plan': plan, 'stop': stop, 'actor': actor,
            'reporter': reporter, 'executor': exe, 'model': model}

        stop.start(model, context)
        path = plan(model, stop, 'Start', context)

        exe.run('inner', path, context)
