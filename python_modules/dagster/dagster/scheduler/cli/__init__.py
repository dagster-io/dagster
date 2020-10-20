import os
import sys

import click
from dagster import __version__
from dagster.scheduler.scheduler import scheduler_run_command


def create_dagster_scheduler_cli():
    commands = {
        "run": scheduler_run_command,
    }

    @click.group(commands=commands)
    @click.version_option(version=__version__)
    def group():
        "CLI tools for working with the dagster scheduler."

    return group


cli = create_dagster_scheduler_cli()


def main():
    cli(obj={})  # pylint:disable=E1123
