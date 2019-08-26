# -*- coding: utf-8 -*-
import subprocess
import sys
import threading
import time

import click


class Spinner:
    '''Spinning CLI prompt, shown while long-running activity is in flight.

    From: https://stackoverflow.com/a/39504463/11295366
    '''

    busy = False
    delay = 0.08
    spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

    @staticmethod
    def spinning_cursor():
        while 1:
            for cursor in Spinner.spinner:
                yield cursor

    def __init__(self, delay=None):
        self.spinner_generator = self.spinning_cursor()
        if delay and float(delay):
            self.delay = delay

    def spinner_task(self):
        while self.busy:
            sys.stdout.write(next(self.spinner_generator))
            sys.stdout.flush()
            time.sleep(self.delay)
            sys.stdout.write('\b')
            sys.stdout.flush()

    def __enter__(self):
        self.busy = True
        threading.Thread(target=self.spinner_task).start()

    def __exit__(self, exception, value, tb):
        self.busy = False
        time.sleep(self.delay)
        if exception is not None:
            return False


class Term:
    ERROR_PREFIX = u'❌  '
    FATAL_PREFIX = u'💣 '
    INFO_PREFIX = u'ℹ️  '
    SUCCESS_PREFIX = u'✅ '
    WAITING_PREFIX = u'⌛ '
    WARNING_PREFIX = u'⚠️  '

    @staticmethod
    def fatal(msg):
        click.echo(click.style(Term.FATAL_PREFIX + msg, fg='red'), err=True)
        sys.exit(1)

    @staticmethod
    def error(msg):
        click.echo(click.style(Term.ERROR_PREFIX + msg, fg='red'))

    @staticmethod
    def info(msg):
        click.echo(click.style(Term.INFO_PREFIX + msg, fg='blue'))

    @staticmethod
    def success(msg):
        click.echo(click.style(Term.SUCCESS_PREFIX + msg, fg='green'))

    @staticmethod
    def waiting(msg):
        click.echo(click.style(Term.WAITING_PREFIX + msg, fg='yellow'))

    @staticmethod
    def warning(msg):
        click.echo(click.style(Term.WARNING_PREFIX + msg, fg='yellow'))


def run_remote_cmd(key_file_path, host, cmd):
    ssh_cmd = 'ssh -i %s ubuntu@%s -t "%s"' % (key_file_path, host, cmd)
    return subprocess.call(ssh_cmd, shell=True)
