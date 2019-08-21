import os
import sys

import click

from ..version import __version__
from ..utils import Features
from .pipeline import create_pipeline_cli_group
from .run import create_run_cli_group
from .schedule import create_schedule_cli_group


def create_dagster_cli():
    commands = {'pipeline': create_pipeline_cli_group(), 'run': create_run_cli_group()}

    if Features.SCHEDULER.is_enabled:
        commands['schedules'] = create_schedule_cli_group()

    @click.group(commands=commands)
    @click.version_option(version=__version__)
    def group():
        'Noop'

    # add the path for the cwd so imports in dynamically loaded code work correctly
    sys.path.append(os.getcwd())
    return group


def main():
    cli = create_dagster_cli()
    cli(obj={})  # pylint:disable=E1123
