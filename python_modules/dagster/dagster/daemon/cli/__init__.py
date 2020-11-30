import os
import sys
import time

import click
import pendulum
from dagster import __version__
from dagster.core.instance import DagsterInstance
from dagster.daemon import DagsterDaemonController


@click.command(
    name="run", help="Run any daemons configured on the DagsterInstance.",
)
def run_command():
    with DagsterInstance.get() as instance:
        controller = DagsterDaemonController(instance)

        while True:
            curr_time = pendulum.now("UTC")
            controller.run_iteration(curr_time)
            time.sleep(0.5)


@click.command(
    name="health-check", help="Check for recent heartbeats from the daemon.",
)
def health_check_command():
    with DagsterInstance.get() as instance:
        if DagsterDaemonController.daemon_healthy(instance):
            click.echo("Daemon healthy")
        else:
            click.echo("Daemon not healthy")
            sys.exit(1)


def create_dagster_daemon_cli():
    commands = {
        "run": run_command,
        "health-check": health_check_command,
    }

    @click.group(commands=commands)
    @click.version_option(version=__version__)
    def group():
        "CLI tools for working with the dagster daemon process."

    return group


cli = create_dagster_daemon_cli()


def main():
    cli(obj={})  # pylint:disable=E1123
