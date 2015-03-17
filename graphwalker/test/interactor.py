# -*- coding: utf-8 -*-
# Copyright (c) 2013 Spotify AB
import fcntl
import select
import subprocess
import sys
import os


class Dummy(object):
    def __getattr__(self, name):
        def f(*al, **kw):
            print ('\033[32m%s\033[0m' % name)
        f.__name__ = name
        return f

    def a(self):
        pass

    def b(self):
        pass


def unblock(fd):
    # make stdin a non-blocking file
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)


class Interactor(object):
    def spawn(self):
        cmd = "%s graphwalker/cli.py" % sys.executable
        cmd += " --planner=Interactive"
        cmd += " --reporter=Print"
        cmd += " --stopcond=Never"
        cmd += " graphwalker/test/examples/ab.graphml"
        cmd += " graphwalker.test.interactor.Dummy"
        self.log('cmd: %r' % cmd)

        self.sub = subprocess.Popen(
            cmd.split(),
            executable=sys.executable,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.join(os.path.dirname(__file__), '../..'))

        unblock(self.sub.stdout.fileno())
        unblock(self.sub.stderr.fileno())

    def log(self, what):
        r = self.context.get('reporter')
        if r:
            r.log('test', what)

    def setup(self, context):
        self.context = context
        self.timeout = context.get('timeout', 0.01)
        self.patience = int(context.get('wait', 2.0) / self.timeout)
        self.last_out = ''
        self.last_err = ''
        self.spawn()

    def push(self, data):
        self.look()
        self.last_out, self.last_err = '', ''
        self.sub.stdin.write(data)

    def look(self):
        r, w, l = select.select(
            [self.sub.stdout, self.sub.stderr], [], [],
            self.timeout)

        if self.sub.stdout in r:
            self.last_out += self.sub.stdout.read()

        if self.sub.stderr in r:
            self.last_err += self.sub.stderr.read()

        return self.last_out, self.last_err

    def expect(self, expectation):
        def show():
            if out:
                print ('out' + ' -' * 30)
                print ('\n    ' + out.strip().replace('\n', '\n    '))
            if err:
                print ('err' + ' -' * 30)
                print ('\n    ' + err.strip().replace('\n', '\n    '))
            if out or err:
                print ('- -' + ' -' * 30)

        if type(expectation) is str:
            x = expectation
            expectation = lambda out, err: x in out or x in err

        for i in range(self.patience):
            out, err = self.look()
            if expectation(out, err):
                show()
                return True
        else:
            show()
            raise AssertionError("Did not find expected output")

    def v_startup(self):
        self.expect(
            lambda out, err: (
                out.startswith('starting ab-') and
                '[stdout]\x1b[32msetup\x1b[0m\n' in out and
                err.startswith('== Currently at: Start')))

    def v_debugger(self):
        self.expect(lambda out, err: err.endswith('(Pdb) '))

    def v_vertex_a(self):
        self.expect(lambda out, err: '== Currently at: a [' in err)

    def v_vertex_b(self):
        self.expect(lambda out, err: '== Currently at: b [' in err)

    def v_break_set_a(self):
        self.push('b\n')
        self.expect(
            lambda out, err: (
                'breakpoint' in err and
                'yes' in err and
                'graphwalker/test/interactor.py:17' in err))

    def v_break_set_b(self):
        self.push('b\n')
        self.expect(
            lambda out, err: (
                'breakpoint' in err and
                'yes' in err and
                'graphwalker/test/interactor.py:20' in err))

    def v_actor_debugger(self):
        self.push('self\n')
        self.expect(
            lambda out, err: (
                '<graphwalker.test.interactor.Dummy object at 0x' in err and
                err.endswith('(Pdb) ')))

    def e_enter(self):
        self.push('\n')
        self.expect('huh?')

    def e_follow_0(self):
        self.push('0\n')
        self.expect(
            lambda out, err: (
                'Begin step' in out and
                '[stdout]\x1b[32mstep_begin\x1b[0m\n' in out and
                '\nPassed step' in out))

    def e_follow_9(self):
        self.push('9\n')
        self.expect('huh?')

    def e_debug(self):
        self.push('d\n')

    def e_continue(self):
        self.push('c\n')

    def e_bug(self):
        self.push('hex(3735928559)\n')
        self.expect('deadbeef')

    def e_bug_set_a(self):
        self.push('self.vert=[v for v in self.g.V.values() if v[1]=="a"][0]\n')

    def e_bug_set_b(self):
        self.push('self.vert=[v for v in self.g.V.values() if v[1]=="b"][0]\n')

    def e_bug_break_a(self):
        self.push('import %s as x\n' % __name__)
        self.push('tbreak x.Dummy.a\n')

    def e_bug_break_b(self):
        self.push('import %s as x\n' % __name__)
        self.push('tbreak x.Dummy.b\n')

    def e_jmp_a(self):
        self.push('j a\n')

    def e_jmp_b(self):
        self.push('j b\n')

    def e_goto_a(self):
        self.push('g a\n')

    def e_goto_b(self):
        self.push('g b\n')
