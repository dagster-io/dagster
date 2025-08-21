import os
import sys
from contextlib import ExitStack
from typing import Optional

import click
from dagster_shared.cli import WorkspaceOpts, workspace_options
from dagster_shared.ipc import interrupt_on_ipc_shutdown_message

from dagster import __version__ as dagster_version
from dagster._cli.utils import assert_no_remaining_opts, get_instance_for_cli
from dagster._cli.workspace.cli_target import workspace_opts_to_load_target
from dagster._core.instance import DagsterInstance, InstanceRef
from dagster._core.telemetry import telemetry_wrapper
from dagster._daemon.controller import (
    DEFAULT_DAEMON_HEARTBEAT_TOLERANCE_SECONDS,
    DagsterDaemonController as DagsterDaemonController,
    all_daemons_live,
    daemon_controller_from_instance,
    debug_daemon_heartbeats,
    get_daemon_statuses,
)
from dagster._daemon.daemon import get_telemetry_daemon_session_id
from dagster._serdes import deserialize_value
from dagster._utils.interrupts import capture_interrupts, setup_interrupt_handlers


def _get_heartbeat_tolerance():
    tolerance = os.getenv(
        "DAGSTER_DAEMON_HEARTBEAT_TOLERANCE",
    )
    return int(tolerance) if tolerance else DEFAULT_DAEMON_HEARTBEAT_TOLERANCE_SECONDS


@click.command(
    name="run",
    help="Run any daemons configured on the DagsterInstance.",
)
@click.option(
    "--code-server-log-level",
    help="Set the log level for any code servers spun up by the daemon.",
    show_default=True,
    default="warning",
    type=click.Choice(["critical", "error", "warning", "info", "debug"], case_sensitive=False),
)
@click.option(
    "--log-level",
    help="Set the log level for any code servers spun up by the daemon.",
    show_default=True,
    default="info",
    type=click.Choice(["critical", "error", "warning", "info", "debug"], case_sensitive=False),
    envvar="DAGSTER_DAEMON_LOG_LEVEL",
)
@click.option(
    "--log-format",
    type=click.Choice(["colored", "json", "rich"], case_sensitive=False),
    show_default=True,
    required=False,
    default="colored",
    help="Format of the log output from the webserver",
)
@click.option(
    "--instance-ref",
    type=click.STRING,
    required=False,
    hidden=True,
)
@click.option(
    "--shutdown-pipe",
    type=click.INT,
    required=False,
    hidden=True,
    help="Internal use only. Pass a readable pipe file descriptor to the daemon process that will be monitored for a shutdown signal.",
)
@workspace_options
def run_command(
    code_server_log_level: str,
    log_level: str,
    log_format: str,
    instance_ref: Optional[str],
    shutdown_pipe: Optional[int],
    **other_opts: object,
) -> None:
    workspace_opts = WorkspaceOpts.extract_from_cli_options(other_opts)
    assert_no_remaining_opts(other_opts)

    # Essential on windows-- will set up windows interrupt signals to raise KeyboardInterrupt
    setup_interrupt_handlers()

    try:
        with ExitStack() as stack:
            if shutdown_pipe:
                stack.enter_context(interrupt_on_ipc_shutdown_message(shutdown_pipe))
            stack.enter_context(capture_interrupts())
            with get_instance_for_cli(
                instance_ref=deserialize_value(instance_ref, InstanceRef) if instance_ref else None
            ) as instance:
                _daemon_run_command(
                    instance, log_level, code_server_log_level, log_format, workspace_opts
                )
    except KeyboardInterrupt:
        return  # Exit cleanly on interrupt


@telemetry_wrapper(metadata={"DAEMON_SESSION_ID": get_telemetry_daemon_session_id()})
def _daemon_run_command(
    instance: DagsterInstance,
    log_level: str,
    code_server_log_level: str,
    log_format: str,
    workspace_opts: WorkspaceOpts,
) -> None:
    with daemon_controller_from_instance(
        instance,
        workspace_load_target=workspace_opts_to_load_target(workspace_opts),
        heartbeat_tolerance_seconds=_get_heartbeat_tolerance(),
        log_level=log_level,
        code_server_log_level=code_server_log_level,
        log_format=log_format,
    ) as controller:
        controller.check_daemon_loop()


@click.command(
    name="liveness-check",
    help="Check for recent heartbeats from the daemon.",
)
def liveness_check_command() -> None:
    with get_instance_for_cli() as instance:
        if all_daemons_live(instance, heartbeat_tolerance_seconds=_get_heartbeat_tolerance()):
            click.echo("Daemon live")
        else:
            click.echo("Daemon(s) not running")
            sys.exit(1)


@click.command(
    name="wipe",
    help="Wipe all heartbeats from storage.",
)
def wipe_command() -> None:
    with get_instance_for_cli() as instance:
        instance.wipe_daemon_heartbeats()
        click.echo("Daemon heartbeats wiped")


@click.command(
    name="heartbeat",
    help="Read and write a heartbeat",
)
def debug_heartbeat_command() -> None:
    with get_instance_for_cli() as instance:
        debug_daemon_heartbeats(instance)


@click.command(
    name="heartbeat-dump",
    help="Log all heartbeat statuses",
)
def debug_heartbeat_dump_command() -> None:
    with get_instance_for_cli() as instance:
        for daemon_status in get_daemon_statuses(instance, instance.get_required_daemon_types()):
            click.echo(daemon_status)


@click.group(
    commands={"heartbeat": debug_heartbeat_command, "heartbeat-dump": debug_heartbeat_dump_command}
)
def debug_group() -> None:
    """Daemon debugging utils."""


def create_dagster_daemon_cli() -> click.Group:
    commands = {
        "run": run_command,
        "liveness-check": liveness_check_command,
        "wipe": wipe_command,
        "debug": debug_group,
    }

    @click.group(commands=commands)
    @click.version_option(version=dagster_version)
    def group():
        """CLI tools for working with the dagster daemon process."""

    return group


cli = create_dagster_daemon_cli()


def main() -> None:
    cli(obj={})
