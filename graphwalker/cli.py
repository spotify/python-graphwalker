#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2013 Spotify AB
import time
import sys

import docopt

from graphwalker import planning
from graphwalker import stopcond
from graphwalker import reporting
from graphwalker import executor
from graphwalker import graph

usage = """\
Usage:
    graphwalker [--reporter=mod.class:a,b,ka=va,kb=vb]...
                [--stopcond=mod.class:a,b,ka=va,kb=vb]
                [--planner=mod.class:a,b,ka=va,kb=vb]...
                [--suite-name=some_random_name]
                [--test-name=some_random_name]
                [--debug]
                [--debugger=mod.class:a,b,ka=va,kb=vb]
                <model> [<actor>]
    graphwalker -h|--help

Model is normally a graph file

Actor is the code module or class

Built-in stopconds, defaults:
  Never
  Seconds       30
  SeenSteps     step,step,step          (also as steps=step,step,step)
  CountSteps    100                     (also as steps=100)
  Coverage      edges=100,verts=0       (verts also as vertices)

  Coverage is the default stop condition.

Built-in planners:
  Random        (default)
  Euler
  Goto          step,step,step
  Interactive

Built-in reporters, defaults:
  Print         output=sys.stdout
  PathRecorder  path=".", name=test name, attach=False
  Cartographer  dotpath=".", imgpath=".", imgtype="png", attach=False
  Attachments   path="."

Debugging:
  --debug       drops you in a debugger if a test fails.
                (set e to None before (c)ontinue, to continue the test
  --debugger=X  set a different debugger, [default: pdb.Pdb]

  Note that --debugger does not imply --debug.

Example:
    graphwalker \\
      --reporter=Print:output=stderr --reporter=Log \\
      --planner=Goto:wake,happy,sad --planner=Interactive \\
      --stop=Coverage:edges=100
      model.dot fleb.Fleb
"""


def run(args):
    sys.path.append('')
    
    reporter = reporting.build(args.get('--reporter') or [])
    suite_name = args.get('--suite-name') or 'graphwalker'

    test_name = args.get('--test-name') or (
        args['<model>'].rsplit('/', 1)[-1].split('.')[0] + '-' +
        time.strftime('%Y%m%d%H%M%S'))

    reporter.start_suite(suite_name)

    plan = planning.build(args.get('--planner') or ['Random'])
    stop = stopcond.build(args.get('--stopcond') or 'Coverage')

    model = graph.Graph.read(args['<model>'])

    actor = args.get('<actor>') or 'graphwalker.dummy.Mute'

    debugger = args.get('--debug') and args.get('--debugger')

    exe = executor.Executor(actor, reporter, debugger)

    context = {'args': args, 'plan': plan, 'stop': stop, 'actor': actor,
               'reporter': reporter, 'executor': exe, 'model': model,
               'debugger': debugger}

    stop.start(model, context)
    path = plan(model, stop, 'Start', context)

    exe.run(test_name, path, context)

    reporter.end_suite()


def main():
    import logging
    import sys

    logging.basicConfig(level=logging.INFO)
    args = docopt.docopt(usage, sys.argv[1:])
    run(args)


if __name__ == '__main__':
    main()
