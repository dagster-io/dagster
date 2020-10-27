import os
import sys

import click
from dagster import __version__

from .run_coordinator_cli import create_run_coordinator_cli_group


def create_dagster_daemon_cli():
    commands = {
        "run-coordinator": create_run_coordinator_cli_group(),
    }

    @click.group(commands=commands)
    @click.version_option(version=__version__)
    def group():
        "CLI tools for working with dagster run coordination daemons."

    return group


cli = create_dagster_daemon_cli()


def main():
    cli(obj={})  # pylint:disable=E1123
