import subprocess
from distutils import spawn
from itertools import groupby

import click


def check_output(cmd, dry_run=True, cwd=None):
    if dry_run:
        click.echo(
            click.style("Dry run; not running.", fg="red") + " Would run: %s" % " ".join(cmd)
        )
        return None
    else:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT, cwd=cwd)


def which_(exe):
    """Uses distutils to look for an executable, mimicking unix which"""
    # https://github.com/PyCQA/pylint/issues/73
    return spawn.find_executable(exe)


def all_equal(iterable):
    g = groupby(iterable)
    return next(g, True) and not next(g, False)
