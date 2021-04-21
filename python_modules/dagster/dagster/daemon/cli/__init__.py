import os
import sys
import threading
import time
import warnings
from contextlib import ExitStack

import click
import pendulum
from dagster import __version__
from dagster.core.instance import DagsterInstance
from dagster.daemon.controller import (
    DAEMON_HEARTBEAT_TOLERANCE_SECONDS,
    DagsterDaemonController,
    all_daemons_healthy,
    all_daemons_live,
    daemon_controller_from_instance,
    debug_daemon_heartbeats,
    get_daemon_status,
)
from dagster.utils.interrupts import capture_interrupts, raise_interrupts_as


@click.command(
    name="run",
    help="Run any daemons configured on the DagsterInstance.",
)
def run_command():
    with capture_interrupts():
        with DagsterInstance.get() as instance:
            if instance.is_ephemeral:
                raise Exception(
                    "dagster-daemon can't run using an in-memory instance. Make sure "
                    "the DAGSTER_HOME environment variable has been set correctly and that "
                    "you have created a dagster.yaml file there."
                )

            with daemon_controller_from_instance(instance) as controller:
                controller.check_daemon_loop()


@click.command(
    name="health-check",
    help="DEPRECATED, use liveness-check instead",
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
    name="liveness-check",
    help="Check for recent heartbeats from the daemon.",
)
def liveness_check_command():
    with DagsterInstance.get() as instance:
        if all_daemons_live(instance):
            click.echo("Daemon live")
        else:
            click.echo("Daemon(s) not running")
            sys.exit(1)


@click.command(
    name="wipe",
    help="Wipe all heartbeats from storage.",
)
def wipe_command():
    with DagsterInstance.get() as instance:
        instance.wipe_daemon_heartbeats()
        click.echo("Daemon heartbeats wiped")


@click.command(
    name="heartbeat",
    help="Read and write a heartbeat",
)
def debug_heartbeat_command():
    with DagsterInstance.get() as instance:
        debug_daemon_heartbeats(instance)


@click.command(
    name="heartbeat-dump",
    help="Log all heartbeat statuses",
)
def debug_heartbeat_dump_command():
    with DagsterInstance.get() as instance:
        for daemon_type in instance.get_required_daemon_types():
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
