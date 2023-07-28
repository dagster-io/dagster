import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import click

import dagster._check as check
from dagster._serdes import serialize_value
from dagster._serdes.ipc import interrupt_ipc_subprocess, open_ipc_subprocess
from dagster._utils.log import configure_loggers

from .job import apply_click_params
from .utils import get_possibly_temporary_instance_for_cli
from .workspace.cli_target import (
    ClickArgValue,
    get_workspace_load_target,
    python_file_option,
    python_module_option,
    working_directory_option,
    workspace_option,
)

_SUBPROCESS_WAIT_TIMEOUT = 60
_CHECK_SUBPROCESS_INTERVAL = 5


def dev_command_options(f):
    return apply_click_params(
        f,
        workspace_option(),
        python_file_option(allow_multiple=True),
        python_module_option(allow_multiple=True),
        working_directory_option(),
    )


@click.command(
    name="dev",
    help=(
        "Start a local deployment of Dagster, including dagster-webserver running on localhost and"
        " the dagster-daemon running in the background"
    ),
    context_settings=dict(
        max_content_width=120,
        help_option_names=["--help"],  # Don't show '-h' since that's the webserver host
    ),
)
@dev_command_options
@click.option(
    "--code-server-log-level",
    help="Set the log level for code servers spun up by dagster services.",
    show_default=True,
    default="warning",
    type=click.Choice(["critical", "error", "warning", "info", "debug"], case_sensitive=False),
)
@click.option(
    "--port",
    "--dagit-port",
    "-p",
    help="Port to use for the Dagster webserver.",
    required=False,
)
@click.option(
    "--host",
    "--dagit-host",
    "-h",
    help="Host to use for the Dagster webserver.",
    required=False,
)
def dev_command(
    code_server_log_level: str,
    port: Optional[str],
    host: Optional[str],
    **kwargs: ClickArgValue,
) -> None:
    # check if dagster-webserver installed, crash if not
    try:
        import dagster_webserver  #  # noqa: F401
    except ImportError:
        raise click.UsageError(
            "The dagster-webserver Python package must be installed in order to use the dagster dev"
            " command. If you're using pip, you can install the dagster-webserver package by"
            ' running "pip install dagster-webserver" in your Python environment.'
        )

    configure_loggers()
    logger = logging.getLogger("dagster")

    # Sanity check workspace args
    get_workspace_load_target(kwargs)

    dagster_home_path = os.getenv("DAGSTER_HOME")

    dagster_yaml_path = os.path.join(os.getcwd(), "dagster.yaml")

    has_local_dagster_yaml = os.path.exists(dagster_yaml_path)
    if dagster_home_path:
        if has_local_dagster_yaml and Path(os.getcwd()) != Path(dagster_home_path):
            logger.warning(
                "Found a dagster instance configuration value (dagster.yaml) in the current"
                " folder, but your DAGSTER_HOME environment variable is set to"
                f" {dagster_home_path}. The dagster.yaml file will not be used to configure Dagster"
                " unless it is placed in the same folder as DAGSTER_HOME."
            )

    with get_possibly_temporary_instance_for_cli("dagster dev", logger=logger) as instance:
        logger.info("Launching Dagster services...")

        args = [
            "--instance-ref",
            serialize_value(instance.get_ref()),
            "--code-server-log-level",
            code_server_log_level,
        ]

        if kwargs.get("workspace"):
            for workspace in check.tuple_elem(kwargs, "workspace"):
                args.extend(["--workspace", workspace])

        if kwargs.get("python_file"):
            for python_file in check.tuple_elem(kwargs, "python_file"):
                args.extend(["--python-file", python_file])

        if kwargs.get("module_name"):
            for module_name in check.tuple_elem(kwargs, "module_name"):
                args.extend(["--module-name", module_name])

        if kwargs.get("working_directory"):
            args.extend(["--working-directory", check.str_elem(kwargs, "working_directory")])

        webserver_process = open_ipc_subprocess(
            [sys.executable, "-m", "dagster_webserver"]
            + (["--port", port] if port else [])
            + (["--host", host] if host else [])
            + args
        )
        daemon_process = open_ipc_subprocess(
            [sys.executable, "-m", "dagster._daemon", "run"] + args
        )
        try:
            while True:
                time.sleep(_CHECK_SUBPROCESS_INTERVAL)

                if webserver_process.poll() is not None:
                    raise Exception(
                        "dagster-webserver process shut down unexpectedly with return code"
                        f" {webserver_process.returncode}"
                    )

                if daemon_process.poll() is not None:
                    raise Exception(
                        "dagster-daemon process shut down unexpectedly with return code"
                        f" {daemon_process.returncode}"
                    )

        except:
            logger.info("Shutting down Dagster services...")
            interrupt_ipc_subprocess(daemon_process)
            interrupt_ipc_subprocess(webserver_process)

            try:
                webserver_process.wait(timeout=_SUBPROCESS_WAIT_TIMEOUT)
            except subprocess.TimeoutExpired:
                logger.warning(
                    "dagster-webserver process did not terminate cleanly, killing the process"
                )
                webserver_process.kill()

            try:
                daemon_process.wait(timeout=_SUBPROCESS_WAIT_TIMEOUT)
            except subprocess.TimeoutExpired:
                logger.warning(
                    "dagster-daemon process did not terminate cleanly, killing the process"
                )
                daemon_process.kill()

            logger.info("Dagster services shut down.")
