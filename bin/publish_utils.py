import os
import subprocess
from collections import defaultdict
from distutils import spawn  # pylint: disable=no-name-in-module
from itertools import groupby

import click


def format_module_versions(module_versions):
    nightlies = defaultdict(list)
    versions = defaultdict(list)

    for module_name, module_version in module_versions.items():
        nightlies[module_version['__nightly__']].append(module_name)
        versions[module_version['__version__']].append(module_name)

    res = '\n'
    for key, libraries in nightlies.items():
        res += '%s:\n\t%s\n\n' % (key, '\n\t'.join(libraries))

    res += '\n'

    for key, libraries in versions.items():
        res += '%s:\n\t%s\n' % (key, '\n\t'.join(libraries))

    return res


def check_output(cmd, dry_run=True):
    if dry_run:
        click.echo(
            click.style('Dry run; not running.', fg='red') + ' Would run: %s' % ' '.join(cmd)
        )
        return None
    else:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT)


def file_relative_path(dunderfile, relative_path):
    '''
    This function is useful when one needs to load a file that is
    relative to the position of the current file. (Such as when
    you encode a configuration file path in source file and want
    in runnable in any current working directory)

    It is meant to be used like the following:

    file_relative_path(__file__, 'path/relative/to/file')

    '''
    return os.path.join(os.path.dirname(dunderfile), relative_path)


def which_(exe):
    '''Uses distutils to look for an executable, mimicking unix which'''
    # https://github.com/PyCQA/pylint/issues/73
    return spawn.find_executable(exe)


def all_equal(iterable):
    g = groupby(iterable)
    return next(g, True) and not next(g, False)
