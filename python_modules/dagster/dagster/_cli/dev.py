import logging
import os
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterator, Sequence
from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import Optional

import click
import yaml
from dagster_shared.cli import workspace_options
from dagster_shared.ipc import (
    get_ipc_shutdown_pipe,
    interrupt_on_ipc_shutdown_message,
    open_ipc_subprocess,
    send_ipc_shutdown_message,
)
from dagster_shared.serdes import serialize_value

from dagster._annotations import deprecated
from dagster._cli.proxy_server_manager import ProxyServerManager
from dagster._cli.utils import assert_no_remaining_opts, get_possibly_temporary_instance_for_cli
from dagster._cli.workspace.cli_target import WorkspaceOpts, workspace_opts_to_load_target
from dagster._core.instance import DagsterInstance
from dagster._utils.interrupts import setup_interrupt_handlers
from dagster._utils.log import configure_loggers

_SUBPROCESS_WAIT_TIMEOUT = 60
_CHECK_SUBPROCESS_INTERVAL = 5


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
@click.option(
    "--live-data-poll-rate",
    help="Rate at which the dagster UI polls for updated asset data (in milliseconds)",
    default="2000",
    show_default=True,
    required=False,
)
@click.option(
    "--use-legacy-code-server-behavior",
    help="Use the legacy behavior of the daemon and webserver each starting up their own code server",
    is_flag=True,
    default=False,
)
@click.option(
    "--shutdown-pipe",
    type=click.INT,
    required=False,
    hidden=True,
    help="Internal use only. Pass a readable pipe file descriptor to the dev process that will be monitored for a shutdown signal.",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="Show verbose stack traces for errors in the code server.",
)
@workspace_options
@deprecated(
    breaking_version="2.0", subject="--dagit-port and --dagit-host args", emit_runtime_warning=False
)
def dev_command(
    code_server_log_level: str,
    log_level: str,
    log_format: str,
    port: Optional[str],
    host: Optional[str],
    live_data_poll_rate: Optional[str],
    use_legacy_code_server_behavior: bool,
    shutdown_pipe: Optional[int],
    verbose: bool,
    **other_opts: object,
) -> None:
    workspace_opts = WorkspaceOpts.extract_from_cli_options(other_opts)
    assert_no_remaining_opts(other_opts)

    dev_command_impl(
        code_server_log_level,
        log_level,
        log_format,
        port,
        host,
        use_legacy_code_server_behavior,
        shutdown_pipe,
        verbose,
        workspace_opts,
        live_data_poll_rate,
    )


def dev_command_impl(
    code_server_log_level: str,
    log_level: str,
    log_format: str,
    port: Optional[str],
    host: Optional[str],
    use_legacy_code_server_behavior: bool,
    shutdown_pipe: Optional[int],
    verbose: bool,
    workspace_opts: WorkspaceOpts,
    live_data_poll_rate: Optional[str] = "2000",
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

    os.environ["DAGSTER_IS_DEV_CLI"] = "1"
    os.environ["DAGSTER_verbose"] = "1" if verbose else ""

    configure_loggers(formatter=log_format, log_level=log_level.upper())
    logger = logging.getLogger("dagster")

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

    # Set up windows interrupt signals to raise KeyboardInterrupt. Note that these handlers are
    # not used if we are using the shutdown pipe.
    setup_interrupt_handlers()

    with ExitStack() as stack:
        if shutdown_pipe:
            stack.enter_context(interrupt_on_ipc_shutdown_message(shutdown_pipe))
        instance = stack.enter_context(
            get_possibly_temporary_instance_for_cli("dagster dev", logger=logger)
        )

        logger.info("Launching Dagster services...")

        with _optionally_create_temp_workspace(
            use_legacy_code_server_behavior=use_legacy_code_server_behavior,
            workspace_opts=workspace_opts,
            instance=instance,
            code_server_log_level=code_server_log_level,
        ) as workspace_args:
            args = [
                "--instance-ref",
                serialize_value(instance.get_ref()),
                "--code-server-log-level",
                code_server_log_level,
                *workspace_args,
            ]

            webserver_read_fd, webserver_write_fd = get_ipc_shutdown_pipe()
            webserver_process = open_ipc_subprocess(
                [sys.executable, "-m", "dagster_webserver"]
                + (["--port", port] if port else [])
                + (["--host", host] if host else [])
                + (["--dagster-log-level", log_level])
                + (["--log-format", log_format])
                + (["--live-data-poll-rate", live_data_poll_rate] if live_data_poll_rate else [])
                + ["--shutdown-pipe", str(webserver_read_fd)]
                + args,
                pass_fds=[webserver_read_fd],
            )

            daemon_read_fd, daemon_write_fd = get_ipc_shutdown_pipe()
            daemon_process = open_ipc_subprocess(
                [
                    sys.executable,
                    "-m",
                    "dagster._daemon",
                    "run",
                    "--log-level",
                    log_level,
                    "--log-format",
                    log_format,
                    "--shutdown-pipe",
                    str(daemon_read_fd),
                ]
                + args,
                pass_fds=[daemon_read_fd],
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

            except KeyboardInterrupt:
                logger.info("KeyboardInterrupt received")
            except:
                logger.exception("An unexpected exception has occurred")
            finally:
                logger.info("Shutting down Dagster services...")
                send_ipc_shutdown_message(webserver_write_fd)
                send_ipc_shutdown_message(daemon_write_fd)

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


@contextmanager
def _temp_grpc_socket_workspace_file(context: "ProxyServerManager") -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_file = Path(temp_dir) / "workspace.yaml"
        workspace_file.write_text(yaml.dump({"load_from": context.get_code_server_specs()}))
        yield workspace_file


@contextmanager
def _optionally_create_temp_workspace(
    *,
    use_legacy_code_server_behavior: bool,
    workspace_opts: WorkspaceOpts,
    instance: DagsterInstance,
    code_server_log_level: str,
) -> Iterator[Sequence[str]]:
    """If not in legacy mode, spin up grpc servers and write a workspace file pointing at them.
    If in legacy mode, do nothing and return the target args.
    """
    if not use_legacy_code_server_behavior:
        with ProxyServerManager(
            instance=instance,
            workspace_load_target=workspace_opts_to_load_target(workspace_opts),
            code_server_log_level=code_server_log_level,
        ) as context:
            with _temp_grpc_socket_workspace_file(context) as workspace_file:
                yield ["--workspace", str(workspace_file)]
    else:
        # sanity check workspace args
        workspace_opts_to_load_target(workspace_opts)
        yield _workspace_opts_to_serialized_cli_args(workspace_opts)


def _workspace_opts_to_serialized_cli_args(workspace_opts: WorkspaceOpts) -> Sequence[str]:
    args = []
    if workspace_opts.empty_workspace:
        args.append("--empty-workspace")

    if workspace_opts.workspace:
        for workspace in workspace_opts.workspace:
            args.extend(("--workspace", workspace))

    if workspace_opts.python_file:
        for python_file in workspace_opts.python_file:
            args.extend(("--python-file", python_file))

    if workspace_opts.module_name:
        for module_name in workspace_opts.module_name:
            args.extend(("--module-name", module_name))

    if workspace_opts.attribute:
        args.extend(("--attribute", workspace_opts.attribute))

    if workspace_opts.working_directory:
        args.extend(("--working-directory", workspace_opts.working_directory))

    if workspace_opts.grpc_port:
        args.extend(("--grpc-port", str(workspace_opts.grpc_port)))

    if workspace_opts.grpc_host:
        args.extend(("--grpc-host", workspace_opts.grpc_host))

    if workspace_opts.grpc_socket:
        args.extend(("--grpc-socket", workspace_opts.grpc_socket))

    if workspace_opts.use_ssl:
        args.append("--use-ssl")

    return args
