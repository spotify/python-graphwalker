#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2015 Spotify AB
"""Tool for testing based on finite state machine graphs.

Graphwalker reads FSMs specified by graphs, plans paths, calls model
methods by name from graph labels and reports progress and results.

While conceptually derived from the Graphwalker project[gw],
(implemented in java) this is a complete reimplementation from that
initial concept.

"""

import argparse
import time

from graphwalker import execution
from graphwalker import graph
from graphwalker import planning
from graphwalker import reporting
from graphwalker import halting

epilog = """

Plugins are generally referenced in the form of "mod.Klass:a,b,ka=va,kb=vb",
for a class Klass in the module mod, instantiated with arguments a and b and
the keyword arguments ka and kb.

""".strip()


class ListAction(argparse.Action):
    """Print list of plugins."""

    def choose_thing(self, option):
        if 'report' in option:
            name, things = 'Reporters', reporting.reporters
        elif 'plan' in option:
            name, things = 'Planners', planning.planners
        elif 'stop' in option or 'cond' in option:
            name, things = 'Stop Conditions', halting.conditions

        return name, things

    def __call__(self, parser, ns, values, option, **kw):
        name, things = self.choose_thing(option)

        print '%s:' % name
        print
        for x in things:
            print '  ' + x.__name__
            print '    ' + x.__doc__.split('\n')[0]
            print

        ns.done = True


def arg_parser():
    parser = argparse.ArgumentParser(epilog=epilog)
    a = parser.add_argument

    a('--suite-name', '--suite', dest='suite', nargs=1)
    a('--test-name', '--test', dest='test', nargs=1)

    a('--reporter', '--reporters', default=[],
      dest='reporters', nargs=1, action='append', metavar='R')

    a('--planner', '--planners',
      dest='planners', nargs=1, action='append', metavar='P')

    a('--stopcond', '--halt', '--halter', '--stop', '--until',
      default='Coverage', dest='stop', metavar='C')

    a('--debugger', dest='debugger', nargs=1, metavar='D')

    a('--debug', action='store_true')

    a('--list-reporters', action=ListAction, nargs=0)
    a('--list-planners', action=ListAction, nargs=0)
    a('--list-stopcond', '--list-halter', action=ListAction, nargs=0)

    a('--dry-run', '-n', dest='done', action='store_true')

    a('modact', nargs='+', metavar='Model or Actor',
      help="Need at least one of each")

    return parser


def load_model_actor(ns):
    model = graph.Graph.read(ns.modact[0])
    for n in ns.modact[1:-1]:
        model = model.combine(graph.Graph.read(n))

    try:
        model = model.combine(graph.Graph.read(ns.modact[-1]))
        actor = 'graphwalker.dummy.Mute'
    except:
        actor = ns.modact[-1]

    return model, actor


def run_context(ns, model, plan, reporter, stop, executor, context, **kw):
    stop.start(model, context)

    path = plan(model, stop, 'Start', context)

    reporter.start_suite(ns.suite)

    executor.run(ns.test, path, context)

    reporter.end_suite()


def build(ns):
    reporter = reporting.build(sum(ns.reporters, []))

    ns.planners = ns.planners or [['Random']]
    plan = planning.build(sum(ns.planners, []))

    stop = halting.build(ns.stop)

    model, actor = load_model_actor(ns)

    debugger = ns.debug and ns.debugger

    exe = execution.Executor(actor, reporter, debugger)

    context = {
        'suite': ns.suite, 'test': ns.test, 'ns': ns,
        'model': model, 'actor': actor, 'debugger': debugger, 'executor': exe,
        'plan': plan, 'stop': stop, 'reporter': reporter,
    }
    context['context'] = context

    return context


def name_test(ns):
    ns.suite = ns.suite or 'graphwalker'

    ns.test = ns.test or (ns.modact and (
        ns.modact[0].rsplit('/', 1)[-1].split('.')[0] + '-') +
        time.strftime('%Y%m%d%H%M%S'))


def main(argv):
    parser = arg_parser()
    ns = parser.parse_args(argv[1:])
    if getattr(ns, 'done', False):
        return 0

    name_test(ns)

    context = build(ns)
    return run_context(**context)


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
