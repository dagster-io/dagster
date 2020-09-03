import os
import sys

import click

from dagster.scheduler.scheduler import scheduler_cli

from ..core.instance import DagsterInstance
from ..version import __version__
from .api import api_cli
from .asset import asset_cli
from .debug import debug_cli
from .instance import instance_cli
from .pipeline import pipeline_cli
from .run import run_cli
from .schedule import schedule_cli


def create_dagster_cli():
    commands = {
        "api": api_cli,
        "pipeline": pipeline_cli,
        "run": run_cli,
        "instance": instance_cli,
        "schedule": schedule_cli,
        "scheduler": scheduler_cli,
        "asset": asset_cli,
        "debug": debug_cli,
    }

    @click.group(commands=commands)
    @click.version_option(version=__version__)
    def group():
        "CLI tools for working with dagster."

    return group


cli = create_dagster_cli()


def main():
    cli(obj={})  # pylint:disable=E1123
