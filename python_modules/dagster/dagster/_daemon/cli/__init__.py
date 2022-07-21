import os
import sys
import threading
import time
import warnings
from contextlib import ExitStack

import click
import pendulum

from dagster import __version__ as dagster_version
from dagster._cli.workspace.cli_target import get_workspace_load_target, workspace_target_argument
from dagster._core.instance import DagsterInstance
from dagster._core.telemetry import telemetry_wrapper
from dagster._daemon.controller import (
    DEFAULT_DAEMON_HEARTBEAT_TOLERANCE_SECONDS,
    DagsterDaemonController,
    all_daemons_healthy,
    all_daemons_live,
    daemon_controller_from_instance,
    debug_daemon_heartbeats,
    get_daemon_statuses,
)
from dagster._daemon.daemon import get_telemetry_daemon_session_id
from dagster._utils.interrupts import capture_interrupts, raise_interrupts_as


def _get_heartbeat_tolerance():
    tolerance = os.getenv(
        "DAGSTER_DAEMON_HEARTBEAT_TOLERANCE",
    )
    return int(tolerance) if tolerance else DEFAULT_DAEMON_HEARTBEAT_TOLERANCE_SECONDS


@click.command(
    name="run",
    help="Run any daemons configured on the DagsterInstance.",
)
@workspace_target_argument
def run_command(**kwargs):
    with capture_interrupts():
        with DagsterInstance.get() as instance:
            _daemon_run_command(instance, kwargs)


@telemetry_wrapper(metadata={"DAEMON_SESSION_ID": get_telemetry_daemon_session_id()})
def _daemon_run_command(instance, kwargs):
    workspace_load_target = get_workspace_load_target(kwargs)

    with daemon_controller_from_instance(
        instance,
        workspace_load_target=workspace_load_target,
        heartbeat_tolerance_seconds=_get_heartbeat_tolerance(),
    ) as controller:
        controller.check_daemon_loop()


@click.command(
    name="liveness-check",
    help="Check for recent heartbeats from the daemon.",
)
def liveness_check_command():
    with DagsterInstance.get() as instance:
        if all_daemons_live(instance, heartbeat_tolerance_seconds=_get_heartbeat_tolerance()):
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
        for daemon_status in get_daemon_statuses(instance, instance.get_required_daemon_types()):
            click.echo(daemon_status)


@click.group(
    commands={"heartbeat": debug_heartbeat_command, "heartbeat-dump": debug_heartbeat_dump_command}
)
def debug_group():
    "Daemon debugging utils"


def create_dagster_daemon_cli():
    commands = {
        "run": run_command,
        "liveness-check": liveness_check_command,
        "wipe": wipe_command,
        "debug": debug_group,
    }

    @click.group(commands=commands)
    @click.version_option(version=dagster_version)
    def group():
        "CLI tools for working with the dagster daemon process."

    return group


cli = create_dagster_daemon_cli()


def main():
    cli(obj={})  # pylint:disable=E1123
