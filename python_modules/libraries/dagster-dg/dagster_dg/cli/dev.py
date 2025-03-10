import os
import signal
import subprocess
import sys
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Optional, TypeVar

import click
import psutil

from dagster_dg.cli.shared_options import dg_global_options
from dagster_dg.cli.utils import create_dagster_cli_cmd
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.error import DgError
from dagster_dg.utils import DgClickCommand, pushd

T = TypeVar("T")

_CHECK_SUBPROCESS_INTERVAL = 5


@click.command(name="dev", cls=DgClickCommand)
@click.option(
    "--code-server-log-level",
    help="Set the log level for code servers spun up by dagster services.",
    show_default=True,
    default="warning",
    type=click.Choice(["critical", "error", "warning", "info", "debug"], case_sensitive=False),
)
@click.option(
    "--log-level",
    help="Set the log level for dagster services.",
    show_default=True,
    default="info",
    type=click.Choice(["critical", "error", "warning", "info", "debug"], case_sensitive=False),
)
@click.option(
    "--log-format",
    type=click.Choice(["colored", "json", "rich"], case_sensitive=False),
    show_default=True,
    required=False,
    default="colored",
    help="Format of the logs for dagster services",
)
@click.option(
    "--port",
    "-p",
    type=int,
    help="Port to use for the Dagster webserver.",
    required=False,
)
@click.option(
    "--host",
    "-h",
    type=str,
    help="Host to use for the Dagster webserver.",
    required=False,
)
@click.option(
    "--live-data-poll-rate",
    help="Rate at which the dagster UI polls for updated asset data (in milliseconds)",
    type=int,
    default=2000,
    show_default=True,
    required=False,
)
@click.option(
    "--verbose",
    "-v",
    flag_value=True,
    default=False,
    help="Show verbose stack traces, including system frames in stack traces.",
)
@dg_global_options
def dev_command(
    code_server_log_level: str,
    log_level: str,
    log_format: str,
    port: Optional[int],
    host: Optional[str],
    live_data_poll_rate: int,
    verbose: bool,
    **global_options: Mapping[str, object],
) -> None:
    """Start a local instance of Dagster.

    If run inside a workspace directory, this command will launch all projects in the
    workspace. If launched inside a project directory, it will launch only that project.
    """
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_workspace_or_project_environment(Path.cwd(), cli_config)

    forward_options = [
        *format_forwarded_option("--code-server-log-level", code_server_log_level),
        *format_forwarded_option("--log-level", log_level),
        *format_forwarded_option("--log-format", log_format),
        *format_forwarded_option("--port", port),
        *format_forwarded_option("--host", host),
        *format_forwarded_option("--live-data-poll-rate", live_data_poll_rate),
        *(["--verbose"] if verbose else []),
    ]

    # In a project context, we can just run `dagster dev` directly, using `dagster` from the
    # code location's environment.
    # In a workspace context, dg dev will construct a temporary
    # workspace file that points at all defined code locations and invoke:
    #     uv tool run --with dagster-webserver dagster dev
    run_cmds = (
        ["uv", "run", "dagster", "dev"]
        if dg_context.is_project
        else ["uv", "tool", "run", "--with", "dagster-webserver", "dagster", "dev"]
    )

    with (
        pushd(dg_context.root_path),
        create_dagster_cli_cmd(dg_context, forward_options, run_cmds=run_cmds) as cmd_object,
    ):
        cmd_location, cmd, workspace_file = cmd_object
        print(f"Using {cmd_location}")  # noqa: T201
        if workspace_file:  # only non-None deployment context
            cmd.extend(["--workspace", workspace_file])
        uv_run_dagster_dev_process = _open_subprocess(cmd)
        try:
            while True:
                time.sleep(_CHECK_SUBPROCESS_INTERVAL)
                if uv_run_dagster_dev_process.poll() is not None:
                    raise DgError(
                        f"dagster-dev process shut down unexpectedly with return code {uv_run_dagster_dev_process.returncode}."
                    )
        except KeyboardInterrupt:
            click.secho(
                "Received keyboard interrupt. Shutting down dagster-dev process.", fg="yellow"
            )
        finally:
            # For reasons not fully understood, directly interrupting the `uv run` process does not
            # work as intended. The interrupt signal is not correctly propagated to the `dagster
            # dev` process, and so that process never shuts down. Therefore, we send the signal
            # directly to the `dagster dev` process (the only child of the `uv run` process). This
            # will cause `dagster dev` to terminate which in turn will cause `uv run` to terminate.
            dagster_dev_pid = _get_child_process_pid(uv_run_dagster_dev_process)
            _interrupt_subprocess(dagster_dev_pid)

            try:
                uv_run_dagster_dev_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                click.secho("`dagster dev` did not terminate in time. Killing it.")
                uv_run_dagster_dev_process.kill()


def format_forwarded_option(option: str, value: object) -> list[str]:
    return [] if value is None else [option, str(value)]


def _get_child_process_pid(proc: "subprocess.Popen") -> int:
    children = psutil.Process(proc.pid).children(recursive=False)
    if len(children) != 1:
        raise ValueError(f"Expected exactly one child process, but found {len(children)}")
    return children[0].pid


# Windows subprocess termination utilities. See here for why we send CTRL_BREAK_EVENT on Windows:
# https://stefan.sofa-rockers.org/2013/08/15/handling-sub-process-hierarchies-python-linux-os-x/


def _interrupt_subprocess(pid: int) -> None:
    """Send CTRL_BREAK_EVENT on Windows, SIGINT on other platforms."""
    if sys.platform == "win32":
        os.kill(pid, signal.CTRL_BREAK_EVENT)
    else:
        os.kill(pid, signal.SIGINT)


def _open_subprocess(command: Sequence[str]) -> "subprocess.Popen":
    """Sets the correct flags to support graceful termination."""
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

    return subprocess.Popen(
        command,
        creationflags=creationflags,
    )
