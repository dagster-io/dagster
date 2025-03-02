import subprocess
import time
from collections.abc import Iterator, Mapping
from contextlib import contextmanager, nullcontext
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional, TypeVar

import click
import yaml

from dagster_dg.cli.shared_options import dg_global_options
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.error import DgError
from dagster_dg.utils import DgClickCommand, exit_with_error, get_venv_executable, pushd
from dagster_dg.utils.ipc import (
    get_ipc_shutdown_pipe,
    interrupt_on_ipc_shutdown_message,
    open_ipc_subprocess,
    send_ipc_shutdown_message,
)

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
    "--shutdown-pipe",
    type=click.INT,
    required=False,
    hidden=True,
    help=(
        "Internal use only. Pass a readable pipe file descriptor to the dg dev process"
        " that will be monitored for a shutdown signal. Useful to interrupt the process in CI."
    ),
)
@dg_global_options
def dev_command(
    code_server_log_level: str,
    log_level: str,
    log_format: str,
    port: Optional[int],
    host: Optional[str],
    live_data_poll_rate: int,
    shutdown_pipe: Optional[int],
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
    ]

    read_fd, write_fd = get_ipc_shutdown_pipe()
    shutdown_pipe_options = ["--shutdown-pipe", str(read_fd)]

    other_options = [*shutdown_pipe_options, *forward_options]

    # In a project context, we can just run `dagster dev` directly, using `dagster` from the
    # project's environment.
    if dg_context.is_project:
        cmd_location = dg_context.get_executable("dagster")
        if dg_context.use_dg_managed_environment:
            cmd = ["uv", "run", "dagster", "dev", *other_options]
        else:
            cmd = [cmd_location, "dev", *other_options]
        temp_workspace_file_cm = nullcontext()

    # In a workspace context with a venv containing dagster and dagster-webserver (both are
    # required for `dagster dev`), we can run `dagster dev` using whatever is installed in the
    # workspace venv.
    elif (
        dg_context.is_workspace
        and dg_context.has_venv
        and dg_context.has_executable("dagster")
        and dg_context.has_executable("dagster-webserver")
    ):
        # --no-project because we might not have the necessary fields in deployment pyproject.toml
        cmd = [
            "uv",
            "run",
            # Unclear why this is necessary, but it seems to be in CI. May be a uv version issue.
            "--python",
            get_venv_executable(dg_context.venv_path),
            "--no-project",
            "dagster",
            "dev",
            *other_options,
        ]
        cmd_location = dg_context.get_executable("dagster")
        temp_workspace_file_cm = temp_workspace_file(dg_context)

    # In a workspace context, dg dev will construct a temporary
    # workspace file that points at all defined code locations and invoke:
    #
    #     uv tool run --with dagster-webserver dagster dev
    #
    # The `--with dagster-webserver` is necessary here to ensure that dagster-webserver is
    # installed in the isolated environment that `uv` will install `dagster` in.
    # `dagster-webserver` is not a dependency of `dagster` but is required to run the `dev`
    # command.
    elif dg_context.is_workspace:
        cmd = [
            "uv",
            "tool",
            "run",
            "--with",
            "dagster-webserver",
            "dagster",
            "dev",
            *other_options,
        ]
        cmd_location = "ephemeral dagster dev"
        temp_workspace_file_cm = temp_workspace_file(dg_context)
    else:
        exit_with_error("This command must be run inside a project or workspace directory.")

    with pushd(dg_context.root_path), temp_workspace_file_cm as workspace_file:
        print(f"Using {cmd_location}")  # noqa: T201
        if workspace_file:  # only non-None workspace context
            cmd.extend(["--workspace", workspace_file])
        uv_run_dagster_dev_process = open_ipc_subprocess(cmd, pass_fds=[read_fd])
        with interrupt_on_ipc_shutdown_message(shutdown_pipe) if shutdown_pipe else nullcontext():
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
                send_ipc_shutdown_message(write_fd)

                try:
                    uv_run_dagster_dev_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    click.secho("`dagster dev` did not terminate in time. Killing it.")
                    uv_run_dagster_dev_process.kill()


@contextmanager
def temp_workspace_file(dg_context: DgContext) -> Iterator[str]:
    with NamedTemporaryFile(mode="w+", delete=True) as temp_workspace_file:
        entries = []
        for project_name in dg_context.get_project_names():
            project_root = dg_context.get_project_path(project_name)
            project_context: DgContext = dg_context.with_root_path(project_root)
            entry = {
                "working_directory": str(dg_context.workspace_root_path),
                "relative_path": str(project_context.definitions_path),
                "location_name": project_context.project_name,
            }
            if project_context.use_dg_managed_environment:
                entry["executable_path"] = str(project_context.project_python_executable)
            entries.append({"python_file": entry})
        yaml.dump({"load_from": entries}, temp_workspace_file)
        temp_workspace_file.flush()
        yield temp_workspace_file.name


def format_forwarded_option(option: str, value: object) -> list[str]:
    return [] if value is None else [option, str(value)]
