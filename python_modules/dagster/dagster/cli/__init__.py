import sys
import os
import click

from ..version import __version__
from .run import create_run_cli_group
from .pipeline import create_pipeline_cli_group


def create_dagster_cli():
    @click.group(commands={'pipeline': create_pipeline_cli_group(), 'run': create_run_cli_group()})
    @click.version_option(version=__version__)
    def group():
        pass

    # add the path for the cwd so imports in dynamically loaded code work correctly
    sys.path.append(os.getcwd())
    return group


def main():
    cli = create_dagster_cli()
    cli(obj={})  # pylint:disable=E1123
