# -*- coding: utf-8 -*-
import os
import subprocess
import sys
import threading
import time
import uuid

import click
import six

from dagster import seven

CURSOR_UP_ONE = '\x1b[1A'
ERASE_LINE = '\x1b[2K'


class Spinner(object):
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


class Term(object):
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

    @staticmethod
    def rewind():
        sys.stdout.write(CURSOR_UP_ONE)
        sys.stdout.write(ERASE_LINE)


def run_remote_cmd(key_file_path, host, cmd, quiet=False):
    ssh_cmd = 'ssh -i %s ubuntu@%s -t "%s"' % (key_file_path, host, cmd)
    if quiet:
        return subprocess.check_output(ssh_cmd, shell=True)
    else:
        return subprocess.call(ssh_cmd, shell=True)


def rsync_to_remote(key_file_path, local_path, remote_host, remote_path):
    remote_user = 'ubuntu'

    rsync_command = [
        'rsync',
        '-avL',
        '--progress',
        # Exclude a few common paths
        '--exclude',
        '\'.pytest_cache\'',
        '--exclude',
        '\'.git\'',
        '--exclude',
        '\'__pycache__\'',
        '--exclude',
        '\'*.pyc\'',
        '-e',
        '"ssh -i %s"' % key_file_path,
        local_path,
        '%s@%s:%s' % (remote_user, remote_host, remote_path),
    ]
    Term.info('rsyncing local path %s to %s:%s' % (local_path, remote_host, remote_path))
    click.echo('\n' + ' '.join(rsync_command) + '\n')
    subprocess.call(' '.join(rsync_command), shell=True)


def remove_ssh_key(key_file_path):
    # We have to clean up after ourselves to avoid "Too many authentication failures" issue.
    Term.waiting('Removing SSH key from authentication agent...')

    # AWS only gives us the private key contents; ssh-add uses the private key for adding but the
    # public key for removing
    try:
        public_keys = six.ensure_str(subprocess.check_output(['ssh-add', '-L'])).strip().split('\n')
    except subprocess.CalledProcessError:
        Term.rewind()
        Term.info('No identities found, skipping')
        return True

    filtered_public_keys = [key for key in public_keys if key_file_path in key]
    public_key = filtered_public_keys[0] if filtered_public_keys else None

    if public_key:
        tmp_pub_file = os.path.join(
            seven.get_system_temp_directory(), uuid.uuid4().hex + '-tmp-pubkey'
        )

        with open(tmp_pub_file, 'wb') as f:
            f.write(six.ensure_binary(public_key))

        res = subprocess.Popen(
            ['ssh-add', '-d', tmp_pub_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        ).communicate()
        res = six.ensure_str(res[0])

        os.unlink(tmp_pub_file)

        if 'Identity removed' in res:
            Term.rewind()
            Term.success('key deleted successfully')
            return True
        else:
            Term.warning('Could not remove key, error: %s' % res)
            return False
    else:
        Term.rewind()
        Term.info('key not found, skipping')
        return False

    return True
