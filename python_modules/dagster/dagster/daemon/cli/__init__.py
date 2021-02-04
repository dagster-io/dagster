import os
import sys
import threading
import time
import warnings

import click
import pendulum
from dagster import __version__
from dagster.core.instance import DagsterInstance
from dagster.daemon.controller import (
    DAEMON_HEARTBEAT_TOLERANCE_SECONDS,
    DagsterDaemonController,
    all_daemons_healthy,
    debug_daemon_heartbeats,
    get_daemon_status,
    required_daemons,
)


@click.command(
    name="run", help="Run any daemons configured on the DagsterInstance.",
)
def run_command():
    with DagsterInstance.get() as instance:
        if instance.is_ephemeral:
            raise Exception(
                "dagster-daemon can't run using an in-memory instance. Make sure "
                "the DAGSTER_HOME environment variable has been set correctly and that "
                "you have created a dagster.yaml file there."
            )

        with DagsterDaemonController(instance) as controller:
            while True:
                # Wait until a daemon has been unhealthy for a long period of time
                # before potentially restarting it due to a hanging or failed daemon
                time.sleep(2 * DAEMON_HEARTBEAT_TOLERANCE_SECONDS)
                controller.check_daemons()


@click.command(
    name="health-check", help="DEPRECATED, use liveness-check instead",
)
def health_check_command():
    warnings.warn("health-check is deprecated. Use liveness-check instead.")
    with DagsterInstance.get() as instance:
        if all_daemons_healthy(instance):
            click.echo("Daemon healthy")
        else:
            click.echo("Daemon not healthy")
            sys.exit(1)


@click.command(
    name="liveness-check", help="Check for recent heartbeats from the daemon.",
)
def liveness_check_command():
    with DagsterInstance.get() as instance:
        if all_daemons_healthy(instance):
            click.echo("Daemon healthy")
        else:
            click.echo("Daemon(s) not running")
            sys.exit(1)


@click.command(
    name="wipe", help="Wipe all heartbeats from storage.",
)
def wipe_command():
    with DagsterInstance.get() as instance:
        instance.wipe_daemon_heartbeats()
        click.echo("Daemon heartbeats wiped")


@click.command(
    name="heartbeat", help="Read and write a heartbeat",
)
def debug_heartbeat_command():
    with DagsterInstance.get() as instance:
        debug_daemon_heartbeats(instance)


@click.command(
    name="heartbeat-dump", help="Log all heartbeat statuses",
)
def debug_heartbeat_dump_command():
    with DagsterInstance.get() as instance:
        for daemon_type in required_daemons(instance):
            click.echo(get_daemon_status(instance, daemon_type))


@click.group(
    commands={"heartbeat": debug_heartbeat_command, "heartbeat-dump": debug_heartbeat_dump_command}
)
def debug_group():
    "Daemon debugging utils"


def create_dagster_daemon_cli():
    commands = {
        "run": run_command,
        "health-check": health_check_command,
        "liveness-check": liveness_check_command,
        "wipe": wipe_command,
        "debug": debug_group,
    }

    @click.group(commands=commands)
    @click.version_option(version=__version__)
    def group():
        "CLI tools for working with the dagster daemon process."

    return group


cli = create_dagster_daemon_cli()


def main():
    cli(obj={})  # pylint:disable=E1123
