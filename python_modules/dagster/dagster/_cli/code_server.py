import json
import logging
import os
import sys
import threading
from typing import Optional

import click
import dagster_shared.seven as seven
from dagster_shared.cli import python_pointer_options
from dagster_shared.serdes.objects.models.defs_state_info import DefsStateInfo

from dagster._cli.utils import assert_no_remaining_opts
from dagster._cli.workspace.cli_target import PythonPointerOpts
from dagster._core.instance import InstanceRef
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.utils import FuturesAwareThreadPoolExecutor
from dagster._serdes import deserialize_value
from dagster._utils.interrupts import setup_interrupt_handlers
from dagster._utils.log import configure_loggers


def get_default_proxy_server_heartbeat_timeout():
    """Get the default heartbeat timeout for the proxy server."""
    return int(os.getenv("DAGSTER_PROXY_SERVER_HEARTBEAT_TIMEOUT", "30"))


DEFAULT_HEARTBEAT_TIMEOUT = get_default_proxy_server_heartbeat_timeout()


@click.group(name="code-server")
def code_server_cli():
    """Commands for working with Dagster code servers."""


@code_server_cli.command(
    name="start",
    help="Start a code server that can serve metadata about a code location and launch runs.",
)
@click.option(
    "--port",
    "-p",
    type=click.INT,
    required=False,
    help="Port over which to serve. You must pass one and only one of --port/-p or --socket/-s.",
    envvar="DAGSTER_CODE_SERVER_PORT",
)
@click.option(
    "--socket",
    "-s",
    type=click.Path(),
    required=False,
    help="Serve over a UDS socket. You must pass one and only one of --port/-p or --socket/-s.",
    envvar="DAGSTER_CODE_SERVER_SOCKET",
)
@click.option(
    "--host",
    "-h",
    type=click.STRING,
    required=False,
    default="localhost",
    help="Hostname at which to serve. Default is localhost.",
    envvar="DAGSTER_CODE_SERVER_HOST",
)
@click.option(
    "--max-workers",
    "-n",
    type=click.INT,
    required=False,
    help="Maximum number of (threaded) workers to use in the code server",
    envvar="DAGSTER_CODE_SERVER_MAX_WORKERS",
)
@click.option(
    "--use-python-environment-entry-point",
    is_flag=True,
    required=False,
    default=False,
    help=(
        "If this flag is set, the server will signal to clients that they should launch "
        "dagster commands using `<this server's python executable> -m dagster`, instead of the "
        "default `dagster` entry point. This is useful when there are multiple Python environments "
        "running in the same machine, so a single `dagster` entry point is not enough to uniquely "
        "determine the environment."
    ),
    envvar="DAGSTER_USE_PYTHON_ENVIRONMENT_ENTRY_POINT",
)
@click.option(
    "--fixed-server-id",
    type=click.STRING,
    required=False,
    help=(
        "[INTERNAL] This option should generally not be used by users. Internal param used by "
        "dagster to spawn a server with the specified server id."
    ),
)
@click.option(
    "--log-level",
    type=click.Choice(["critical", "error", "warning", "info", "debug"], case_sensitive=False),
    show_default=True,
    required=False,
    default="info",
    help="Level at which to log output from the code server process",
)
@click.option(
    "--log-format",
    type=click.Choice(["colored", "json", "rich"], case_sensitive=False),
    show_default=True,
    required=False,
    default="colored",
    help="Format of the log output from the code server process",
)
@click.option(
    "--container-image",
    type=click.STRING,
    required=False,
    help="Container image to use to run code from this server.",
    envvar="DAGSTER_CONTAINER_IMAGE",
)
@click.option(
    "--container-context",
    type=click.STRING,
    required=False,
    help=(
        "Serialized JSON with configuration for any containers created to run the "
        "code from this server."
    ),
    envvar="DAGSTER_CONTAINER_CONTEXT",
)
@click.option(
    "--inject-env-vars-from-instance",
    is_flag=True,
    required=False,
    default=False,
    help="Whether to load env vars from the instance and inject them into the environment.",
    envvar="DAGSTER_INJECT_ENV_VARS_FROM_INSTANCE",
)
@click.option(
    "--location-name",
    type=click.STRING,
    required=False,
    help="Name of the code location this server corresponds to.",
    envvar="DAGSTER_LOCATION_NAME",
)
@click.option(
    "--startup-timeout",
    type=click.INT,
    required=False,
    default=0,
    help="How long to wait for code to load or reload before timing out. Defaults to no timeout.",
    envvar="DAGSTER_CODE_SERVER_STARTUP_TIMEOUT",
)
@click.option(
    "--heartbeat",
    is_flag=True,
    default=False,
    help=(
        "If set, the GRPC server will shut itself down when it fails to receive a heartbeat "
        "after a timeout configurable with --heartbeat-timeout."
    ),
)
@click.option(
    "--heartbeat-timeout",
    type=click.INT,
    required=False,
    default=DEFAULT_HEARTBEAT_TIMEOUT,
    help="How long to wait for a heartbeat from the caller before timing out. Only comes into play if --heartbeat is set. Defaults to 30 seconds.",
)
@click.option(
    "--instance-ref",
    type=click.STRING,
    required=False,
    help="[INTERNAL] Serialized InstanceRef to use for accessing the instance",
    envvar="DAGSTER_INSTANCE_REF",
)
@click.option(
    "--defs-state-info",
    type=click.STRING,
    required=False,
    help="[INTERNAL] Serialized DefsStateInfo to use for accessing the state versions",
)
@python_pointer_options
def start_command(
    port: Optional[int],
    socket: Optional[str],
    host: str,
    max_workers: Optional[int],
    use_python_environment_entry_point: bool,
    fixed_server_id: Optional[str],
    log_level: str,
    log_format: str,
    container_image: Optional[str],
    container_context: Optional[str],
    inject_env_vars_from_instance: bool,
    location_name: Optional[str],
    startup_timeout: int,
    heartbeat: bool,
    heartbeat_timeout,
    instance_ref: Optional[str],
    defs_state_info: Optional[str],
    **other_opts,
):
    # deferring for import perf
    from dagster._grpc.proxy_server import DagsterProxyApiServicer
    from dagster._grpc.server import DagsterGrpcServer

    python_pointer_opts = PythonPointerOpts.extract_from_cli_options(other_opts)
    assert_no_remaining_opts(other_opts)

    if seven.IS_WINDOWS and port is None:
        raise click.UsageError(
            "You must pass a valid --port/-p on Windows: --socket/-s not supported."
        )
    if not (port or (socket and not (port and socket))):
        raise click.UsageError("You must pass one and only one of --port/-p or --socket/-s.")

    setup_interrupt_handlers()

    configure_loggers(formatter=log_format, log_level=log_level.upper())
    logger = logging.getLogger("dagster.code_server")

    container_image = container_image or os.getenv("DAGSTER_CURRENT_IMAGE")

    # in the gRPC api CLI we never load more than one module or python file at a time
    loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable if use_python_environment_entry_point else None,
        attribute=python_pointer_opts.attribute,
        working_directory=python_pointer_opts.working_directory or os.getcwd(),
        module_name=python_pointer_opts.module_name,
        python_file=python_pointer_opts.python_file,
        package_name=python_pointer_opts.package_name,
        autoload_defs_module_name=python_pointer_opts.autoload_defs_module_name,
    )

    code_desc = " "
    if loadable_target_origin.python_file:
        code_desc = f" for file {loadable_target_origin.python_file} "
    elif loadable_target_origin.package_name:
        code_desc = f" for package {loadable_target_origin.package_name} "
    elif loadable_target_origin.module_name:
        code_desc = f" for module {loadable_target_origin.module_name} "

    server_desc = (
        f"Dagster code proxy server{code_desc}on port {port} in process {os.getpid()}"
        if port
        else f"Dagster code proxy server{code_desc}in process {os.getpid()}"
    )

    logger.info("Starting %s", server_desc)

    server_termination_event = threading.Event()

    threadpool_executor = FuturesAwareThreadPoolExecutor(max_workers=max_workers)
    api_servicer = DagsterProxyApiServicer(
        loadable_target_origin=loadable_target_origin,
        fixed_server_id=fixed_server_id,
        container_image=container_image,
        container_context=(
            json.loads(container_context) if container_context is not None else None
        ),
        inject_env_vars_from_instance=inject_env_vars_from_instance,
        location_name=location_name,
        log_level=log_level,
        startup_timeout=startup_timeout,
        instance_ref=deserialize_value(instance_ref, InstanceRef) if instance_ref else None,
        server_termination_event=server_termination_event,
        logger=logger,
        server_heartbeat=heartbeat,
        server_heartbeat_timeout=heartbeat_timeout,
        defs_state_info=deserialize_value(defs_state_info, DefsStateInfo)
        if defs_state_info
        else None,
    )
    server = DagsterGrpcServer(
        server_termination_event=server_termination_event,
        dagster_api_servicer=api_servicer,
        port=port,
        socket=socket,
        host=host,
        threadpool_executor=threadpool_executor,
        logger=logger,
    )

    logger.info("Started %s", server_desc)

    try:
        server.serve()
    except KeyboardInterrupt:
        # Terminate cleanly on interrupt
        logger.info("Code proxy server was interrupted")
    finally:
        logger.info("Shutting down %s", server_desc)
