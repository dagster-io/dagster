import os
import sys

import click

from ..core.instance import DagsterInstance
from ..version import __version__
from .instance import instance_cli
from .pipeline import pipeline_cli
from .run import run_cli
from .schedule import schedule_cli
from .utils import utils_cli


def create_dagster_cli():
    commands = {
        'pipeline': pipeline_cli,
        'run': run_cli,
        'instance': instance_cli,
        'schedule': schedule_cli,
        'utils': utils_cli,
    }

    @click.group(commands=commands)
    @click.version_option(version=__version__)
    def group():
        'CLI tools for working with dagster.'

    # add the path for the cwd so imports in dynamically loaded code work correctly
    sys.path.append(os.getcwd())
    return group


cli = create_dagster_cli()


def main():
    cli(obj={})  # pylint:disable=E1123
