import os
import sys

import click

from ..core.instance import DagsterInstance
from ..version import __version__
from .api import api_cli
from .asset import asset_cli
from .debug import debug_cli
from .instance import instance_cli
from .new_repo import new_repo_cli
from .pipeline import pipeline_cli
from .run import run_cli
from .schedule import schedule_cli
from .sensor import sensor_cli


def create_dagster_cli():
    commands = {
        "api": api_cli,
        "pipeline": pipeline_cli,
        "run": run_cli,
        "instance": instance_cli,
        "schedule": schedule_cli,
        "sensor": sensor_cli,
        "asset": asset_cli,
        "debug": debug_cli,
        "new-repo": new_repo_cli,
    }

    @click.group(commands=commands)
    @click.version_option(version=__version__)
    def group():
        "CLI tools for working with dagster."

    return group


ENV_PREFIX = "DAGSTER_CLI"
cli = create_dagster_cli()


def main():
    cli(auto_envvar_prefix=ENV_PREFIX)  # pylint:disable=E1123
