import json
import os
import signal
import subprocess
import sys
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Optional, TypeVar

import click

from dagster_dg.check import check_yaml as check_yaml_fn
from dagster_dg.cli.shared_options import dg_global_options
from dagster_dg.cli.utils import create_dagster_cli_cmd
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.error import DgError
from dagster_dg.utils import DgClickCommand, pushd, strip_activated_venv_from_env_vars
from dagster_dg.utils.cli import format_forwarded_option
from dagster_dg.utils.telemetry import cli_telemetry_wrapper

T = TypeVar("T")

_CHECK_SUBPROCESS_INTERVAL = 5
_SUBPROCESS_WAIT_TIMEOUT = 60


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
    "--check-yaml/--no-check-yaml",
    flag_value=True,
    default=True,
    help="Whether to schema-check component.yaml files for the project before starting the dev server.",
)
@dg_global_options
@cli_telemetry_wrapper
def dev_command(
    code_server_log_level: str,
    log_level: str,
    log_format: str,
    port: Optional[int],
    host: Optional[str],
    live_data_poll_rate: int,
    check_yaml: bool,
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
        *(["--verbose"] if dg_context.config.cli.verbose else []),
    ]

    if dg_context.is_workspace:
        os.environ["DAGSTER_PROJECT_ENV_FILE_PATHS"] = json.dumps(
            {
                dg_context.with_root_path(
                    dg_context.workspace_root_path / project.path
                ).code_location_name: str(project.path)
                for project in dg_context.project_specs
            }
        )
    else:
        os.environ["DAGSTER_PROJECT_ENV_FILE_PATHS"] = json.dumps(
            {dg_context.code_location_name: str(dg_context.root_path)}
        )

    # In a project context, we can just run `dagster dev` directly, using `dagster` from the
    # code location's environment.
    # In a workspace context, dg dev will construct a temporary
    # workspace file that points at all defined code locations and invoke:
    #     uv tool run --with dagster-webserver dagster dev
    if dg_context.use_dg_managed_environment:
        run_cmds = ["uv", "run", "dagster", "dev"]
    elif dg_context.is_project:
        run_cmds = ["dagster", "dev"]
    else:
        run_cmds = ["uv", "tool", "run", "--with", "dagster-webserver", "dagster", "dev"]

    with (
        pushd(dg_context.root_path),
        create_dagster_cli_cmd(dg_context, forward_options, run_cmds=run_cmds) as cmd_object,
    ):
        if check_yaml:
            overall_check_result = True
            project_dirs = (
                [project.path for project in dg_context.project_specs]
                if dg_context.is_workspace
                else [dg_context.root_path]
            )
            for project_dir in project_dirs:
                check_result = check_yaml_fn(
                    dg_context.for_project_environment(project_dir, cli_config),
                    [],
                )
                overall_check_result = overall_check_result and check_result
            if not overall_check_result:
                click.get_current_context().exit(1)

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
            _interrupt_subprocess(uv_run_dagster_dev_process.pid)

            try:
                uv_run_dagster_dev_process.wait(timeout=_SUBPROCESS_WAIT_TIMEOUT)
            except subprocess.TimeoutExpired:
                click.secho("`dagster dev` did not terminate in time. Killing it.")
                uv_run_dagster_dev_process.kill()


# Windows subprocess termination utilities. See here for why we send CTRL_BREAK_EVENT on Windows:
# https://stefan.sofa-rockers.org/2013/08/15/handling-sub-process-hierarchies-python-linux-os-x/


def _interrupt_subprocess(pid: int) -> None:
    """Send CTRL_BREAK_EVENT on Windows, SIGINT on other platforms."""
    if sys.platform == "win32":
        os.kill(pid, signal.CTRL_BREAK_EVENT)
    else:
        # uv tool run appears to forward SIGTERM but not SIGINT - see https://github.com/astral-sh/uv/issues/12108
        os.kill(pid, signal.SIGTERM)


def _open_subprocess(command: Sequence[str]) -> "subprocess.Popen":
    """Sets the correct flags to support graceful termination."""
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

    return subprocess.Popen(
        command,
        creationflags=creationflags,
        env=strip_activated_venv_from_env_vars(os.environ),
    )
