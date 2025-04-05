import logging
import os
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Iterator, Mapping, Sequence
from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import Any, Optional

import click
import yaml
from dagster_shared.ipc import (
    get_ipc_shutdown_pipe,
    interrupt_on_ipc_shutdown_message,
    open_ipc_subprocess,
    send_ipc_shutdown_message,
)
from dagster_shared.serdes import serialize_value
from typing_extensions import Self

import dagster._check as check
from dagster._annotations import deprecated
from dagster._cli.utils import assert_no_remaining_opts, get_possibly_temporary_instance_for_cli
from dagster._cli.workspace.cli_target import WorkspaceOpts, workspace_options
from dagster._core.errors import DagsterUserCodeUnreachableError
from dagster._core.instance import DagsterInstance
from dagster._core.remote_representation import CodeLocationOrigin
from dagster._core.remote_representation.grpc_server_registry import (
    GrpcServerEndpoint,
    GrpcServerRegistry,
)
from dagster._core.remote_representation.origin import (
    GrpcServerCodeLocationOrigin,
    ManagedGrpcPythonEnvCodeLocationOrigin,
)
from dagster._core.workspace.context import WEBSERVER_GRPC_SERVER_HEARTBEAT_TTL
from dagster._core.workspace.load_target import WorkspaceLoadTarget
from dagster._core.workspace.workspace import CurrentWorkspace
from dagster._grpc.client import CLIENT_HEARTBEAT_INTERVAL
from dagster._grpc.server import INCREASE_TIMEOUT_DAGSTER_YAML_MSG, GrpcServerCommand
from dagster._utils.interrupts import setup_interrupt_handlers
from dagster._utils.log import configure_loggers

_SUBPROCESS_WAIT_TIMEOUT = 60
_CHECK_SUBPROCESS_INTERVAL = 5


def get_auto_restart_code_server_interval() -> int:
    return int(os.getenv("DAGSTER_CODE_SERVER_AUTO_RESTART_INTERVAL", "30"))


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
def _temp_grpc_socket_workspace_file(context: "DagsterDevCodeServerManager") -> Iterator[Path]:
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
        with DagsterDevCodeServerManager(
            instance=instance,
            workspace_load_target=workspace_opts.to_load_target(),
            server_command=GrpcServerCommand.CODE_SERVER_START,
            code_server_log_level=code_server_log_level,
        ) as context:
            with _temp_grpc_socket_workspace_file(context) as workspace_file:
                yield ["--workspace", str(workspace_file)]
    else:
        # sanity check workspace args
        workspace_opts.to_load_target()
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


class DagsterDevCodeServerManager:
    """Context manager that manages the lifecycle of code servers launched by the dagster dev command."""

    def __init__(
        self,
        instance: DagsterInstance,
        workspace_load_target: Optional[WorkspaceLoadTarget],
        code_server_log_level: str = "INFO",
        server_command: GrpcServerCommand = GrpcServerCommand.API_GRPC,
    ) -> None:
        self._stack = ExitStack()

        self._instance = check.inst_param(instance, "instance", DagsterInstance)
        self._workspace_load_target = check.opt_inst_param(
            workspace_load_target, "workspace_load_target", WorkspaceLoadTarget
        )

        self._grpc_server_registry: GrpcServerRegistry = self._stack.enter_context(
            GrpcServerRegistry(
                instance_ref=self._instance.get_ref(),
                server_command=server_command,
                heartbeat_ttl=WEBSERVER_GRPC_SERVER_HEARTBEAT_TTL,
                startup_timeout=instance.code_server_process_startup_timeout,
                log_level=code_server_log_level,
                wait_for_processes_on_shutdown=instance.wait_for_local_code_server_processes_on_shutdown,
                additional_timeout_msg=INCREASE_TIMEOUT_DAGSTER_YAML_MSG,
            )
        )

        self._current_workspace: CurrentWorkspace = CurrentWorkspace(code_location_entries={})
        # Is it ok that there's only one of these? When would this be something that needs to be called per location?
        self.__shutdown_event = threading.Event()
        self.__auto_restart_thread = threading.Thread(target=self.auto_restart_thread, daemon=True)
        self.__auto_restart_thread.start()

    def auto_restart_thread(self) -> None:
        """Thread that automatically restarts the code server if it is not responding."""
        while True:
            self.__shutdown_event.wait(get_auto_restart_code_server_interval())
            if self.__shutdown_event.is_set():
                break
            for process in self._grpc_server_registry.all_processes:
                if process.server_process.poll() is not None:
                    logging.getLogger(__name__).warning(
                        f"Code server process has exited with code {process.server_process.poll()}. Restarting the code server process."
                    )
                    process.start_server_process()

    def client_heartbeat_thread(self) -> None:
        while True:
            self.__shutdown_event.wait(CLIENT_HEARTBEAT_INTERVAL)
            if self.__shutdown_event.is_set():
                break
            for process in self._grpc_server_registry.all_processes:
                client = process.create_client()
                try:
                    client.heartbeat("ping")
                except DagsterUserCodeUnreachableError:
                    continue

    @property
    def _origins(self) -> Sequence[CodeLocationOrigin]:
        return self._workspace_load_target.create_origins() if self._workspace_load_target else []

    def retrieve_endpoint(
        self, origin: CodeLocationOrigin, reload: bool = False
    ) -> GrpcServerEndpoint:
        return (
            self._grpc_server_registry.reload_grpc_endpoint(origin)
            if reload
            else self._grpc_server_registry.get_grpc_endpoint(origin)
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exception_type, exception_value, traceback) -> None:
        self.__shutdown_event.set()
        self.empty_workspace()  # update to empty to close all current locations
        self._stack.close()

    def empty_workspace(self) -> None:
        """Empty the workspace by closing all code locations."""
        for entry in self._current_workspace.code_location_entries.values():
            if entry.code_location:
                entry.code_location.cleanup()

    def get_code_server_specs(self) -> Sequence[Mapping[str, Mapping[str, Any]]]:
        result = []
        for origin in self._origins:
            if isinstance(origin, ManagedGrpcPythonEnvCodeLocationOrigin):
                grpc_endpoint = self._grpc_server_registry.get_grpc_endpoint(origin)
                server_spec = {
                    "location_name": origin.location_name,
                    "socket": grpc_endpoint.socket,
                    "port": grpc_endpoint.port,
                    "host": grpc_endpoint.host,
                    "additional_metadata": origin.loadable_target_origin.as_dict,
                }
            elif isinstance(origin, GrpcServerCodeLocationOrigin):
                server_spec = {
                    "location_name": origin.location_name,
                    "host": origin.host,
                    "port": origin.port,
                    "socket": origin.socket,
                    "additional_metadata": origin.additional_metadata,
                }
            else:
                check.failed(f"Unexpected origin type {origin}")
            result.append({"grpc_server": {k: v for k, v in server_spec.items() if v is not None}})
        return result
