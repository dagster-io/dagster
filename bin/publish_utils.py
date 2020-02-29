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


def which_(exe):
    '''Uses distutils to look for an executable, mimicking unix which'''
    # https://github.com/PyCQA/pylint/issues/73
    return spawn.find_executable(exe)


def all_equal(iterable):
    g = groupby(iterable)
    return next(g, True) and not next(g, False)
