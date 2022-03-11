import os
import sys

import click

from ..core.instance import DagsterInstance
from ..version import __version__
from .api import api_cli
from .asset import asset_cli
from .debug import debug_cli
from .instance import instance_cli
from .job import job_cli
from .new_project import new_project_cli
from .pipeline import pipeline_cli
from .run import run_cli
from .schedule import schedule_cli
from .sensor import sensor_cli


def create_dagster_cli():
    commands = {
        "api": api_cli,
        "pipeline": pipeline_cli,
        "job": job_cli,
        "run": run_cli,
        "instance": instance_cli,
        "schedule": schedule_cli,
        "sensor": sensor_cli,
        "asset": asset_cli,
        "debug": debug_cli,
        "new-project": new_project_cli,
    }

    @click.group(
        commands=commands,
        context_settings={"max_content_width": 120, "help_option_names": ["-h", "--help"]},
    )
    @click.version_option(__version__, "--version", "-v")
    def group():
        "CLI tools for working with Dagster."

    return group


ENV_PREFIX = "DAGSTER_CLI"
cli = create_dagster_cli()


def main():
    cli(auto_envvar_prefix=ENV_PREFIX)  # pylint:disable=E1123
