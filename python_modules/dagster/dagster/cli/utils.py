from __future__ import print_function

import sys

import click
import six

from dagster import check
from dagster.core.execution.compute_logs import tail_polling
from dagster.core.telemetry import (
    execute_disable_telemetry,
    execute_enable_telemetry,
    execute_reset_telemetry_profile,
)


def create_utils_cli_group():
    group = click.Group(name="utils")
    group.add_command(tail_command)
    group.add_command(disable_telemetry)
    group.add_command(enable_telemetry)
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


@click.command(
    name='disable_telemetry',
    help='Update $DAGSTER_HOME/dagster.yaml to disable telemetry. Requires $DAGSTER_HOME to be set \
        For more information, check out the docs at \
        https://docs.dagster.io/latest/install/telemetry/',
)
def disable_telemetry():
    execute_disable_telemetry()


@click.command(
    name='enable_telemetry',
    help='Update $DAGSTER_HOME/dagster.yaml to enable telemetry. Requires $DAGSTER_HOME to be set \
        For more information, check out the docs at \
        https://docs.dagster.io/latest/install/telemetry/',
)
@click.option('--reset', help='Generate a new user identifier for telemetry.', is_flag=True)
def enable_telemetry(reset):
    if reset:
        execute_reset_telemetry_profile()

    execute_enable_telemetry()


utils_cli = create_utils_cli_group()
