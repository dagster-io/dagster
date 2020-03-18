from __future__ import print_function

import sys

import click
import six

from dagster import check
from dagster.core.execution.compute_logs import tail_polling


def create_utils_cli_group():
    group = click.Group(name="utils")
    group.add_command(tail_command)
    return group


def extract_string_param(name, value):
    if value and not isinstance(value, six.string_types):
        if len(value) == 1:
            return value[0]
        else:
            check.failed(
                'Can only handle zero or one {name} args. Got {value}'.format(
                    name=repr(name), value=repr(value)
                )
            )
    return value


@click.command(name='tail', help='Cross-platform file tailing')
@click.argument('filepath')
@click.option('--parent-pid', help="Process pid to watch for termination")
@click.option('--io-type', help="Whether to stream to stdout/stderr", default='stdout')
def tail_command(filepath, parent_pid, io_type):
    filepath = extract_string_param('filepath', filepath)
    parent_pid = extract_string_param('parent_pid', parent_pid)
    io_type = extract_string_param('io_type', io_type)
    stream = sys.stdout if io_type == 'stdout' else sys.stderr
    tail_polling(filepath, stream, parent_pid)


utils_cli = create_utils_cli_group()
