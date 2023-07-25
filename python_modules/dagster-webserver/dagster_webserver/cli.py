import asyncio
import logging
import os
import sys
import textwrap
from typing import Optional

import click
import dagster._check as check
import uvicorn
from dagster._cli.utils import get_possibly_temporary_instance_for_cli
from dagster._cli.workspace import (
    get_workspace_process_context_from_kwargs,
    workspace_target_argument,
)
from dagster._cli.workspace.cli_target import WORKSPACE_TARGET_WARNING, ClickArgValue
from dagster._core.instance import InstanceRef
from dagster._core.telemetry import START_DAGSTER_WEBSERVER, log_action
from dagster._core.telemetry_upload import uploading_logging_thread
from dagster._core.workspace.context import (
    IWorkspaceProcessContext,
)
from dagster._serdes import deserialize_value
from dagster._utils import DEFAULT_WORKSPACE_YAML_FILENAME, find_free_port, is_port_in_use
from dagster._utils.log import configure_loggers

from .app import create_app_from_workspace_process_context
from .version import __version__


def create_dagster_webserver_cli():
    return dagster_webserver


# If the user runs `dagit` from the command line, we update this to "dagit"
WEBSERVER_LOGGER_NAME = "dagster-webserver"

DEFAULT_WEBSERVER_HOST = "127.0.0.1"
DEFAULT_WEBSERVER_PORT = 3000

DEFAULT_DB_STATEMENT_TIMEOUT = 15000  # 15 sec
DEFAULT_POOL_RECYCLE = 3600  # 1 hr


@click.command(
    name="dagster-webserver",
    help=textwrap.dedent(
        f"""
        Run dagster-webserver. Loads a code location.

        {WORKSPACE_TARGET_WARNING}

        Examples:

        1. dagster-webserver (works if ./{DEFAULT_WORKSPACE_YAML_FILENAME} exists)

        2. dagster-webserver -w path/to/{DEFAULT_WORKSPACE_YAML_FILENAME}

        3. dagster-webserver -f path/to/file.py

        4. dagster-webserver -f path/to/file.py -d path/to/working_directory

        5. dagster-webserver -m some_module

        6. dagster-webserver -f path/to/file.py -a define_repo

        7. dagster-webserver -m some_module -a define_repo

        8. dagster-webserver -p 3333

        Options can also provide arguments via environment variables prefixed with DAGSTER_WEBSERVER.

        For example, DAGSTER_WEBSERVER_PORT=3333 dagster-webserver
    """
    ),
)
@workspace_target_argument
@click.option(
    "--host",
    "-h",
    type=click.STRING,
    default=DEFAULT_WEBSERVER_HOST,
    help="Host to run server on",
    show_default=True,
)
@click.option(
    "--port",
    "-p",
    type=click.INT,
    help=f"Port to run server on - defaults to {DEFAULT_WEBSERVER_PORT}",
    default=None,
    show_default=True,
)
@click.option(
    "--path-prefix",
    "-l",
    type=click.STRING,
    default="",
    help="The path prefix where server will be hosted (eg: /dagster-webserver)",
    show_default=True,
)
@click.option(
    "--db-statement-timeout",
    help=(
        "The timeout in milliseconds to set on database statements sent "
        "to the DagsterInstance. Not respected in all configurations."
    ),
    default=DEFAULT_DB_STATEMENT_TIMEOUT,
    type=click.INT,
    show_default=True,
)
@click.option(
    "--db-pool-recycle",
    help=(
        "The maximum age of a connection to use from the sqlalchemy pool without connection"
        " recycling. Set to -1 to disable. Not respected in all configurations."
    ),
    default=DEFAULT_POOL_RECYCLE,
    type=click.INT,
    show_default=True,
)
@click.option(
    "--read-only",
    help=(
        "Start server in read-only mode, where all mutations such as launching runs and "
        "turning schedules on/off are turned off."
    ),
    is_flag=True,
)
@click.option(
    "--suppress-warnings",
    help="Filter all warnings when hosting server.",
    is_flag=True,
)
@click.option(
    "--log-level",
    help="Set the log level for the uvicorn web server.",
    show_default=True,
    default="warning",
    type=click.Choice(
        ["critical", "error", "warning", "info", "debug", "trace"], case_sensitive=False
    ),
)
@click.option(
    "--code-server-log-level",
    help="Set the log level for any code servers spun up by the webserver.",
    show_default=True,
    default="info",
    type=click.Choice(["critical", "error", "warning", "info", "debug"], case_sensitive=False),
)
@click.option(
    "--instance-ref",
    type=click.STRING,
    required=False,
    hidden=True,
)
@click.version_option(version=__version__, prog_name="dagster-webserver")
def dagster_webserver(
    host: str,
    port: int,
    path_prefix: str,
    db_statement_timeout: int,
    db_pool_recycle: int,
    read_only: bool,
    suppress_warnings: bool,
    log_level: str,
    code_server_log_level: str,
    instance_ref: Optional[str],
    **kwargs: ClickArgValue,
):
    if suppress_warnings:
        os.environ["PYTHONWARNINGS"] = "ignore"

    configure_loggers()
    logger = logging.getLogger(WEBSERVER_LOGGER_NAME)

    if sys.argv[0].endswith("dagit"):
        logger.warning(
            "The `dagit` CLI command is deprecated and will be removed in dagster 2.0. Please use"
            " `dagster-webserver` instead."
        )

    with get_possibly_temporary_instance_for_cli(
        cli_command="dagster-webserver",
        instance_ref=deserialize_value(instance_ref, InstanceRef) if instance_ref else None,
        logger=logger,
    ) as instance:
        # Allow the instance components to change behavior in the context of a long running server process
        instance.optimize_for_webserver(db_statement_timeout, db_pool_recycle)

        with get_workspace_process_context_from_kwargs(
            instance,
            version=__version__,
            read_only=read_only,
            kwargs=kwargs,
            code_server_log_level=code_server_log_level,
        ) as workspace_process_context:
            host_dagster_ui_with_workspace_process_context(
                workspace_process_context, host, port, path_prefix, log_level
            )


async def _lifespan(app):
    # workaround from https://github.com/encode/uvicorn/issues/1160 for termination
    try:
        yield
    except asyncio.exceptions.CancelledError:
        logging.getLogger(WEBSERVER_LOGGER_NAME).info(
            f"Server for {WEBSERVER_LOGGER_NAME} was shut down."
        )
        # Expected error when dagster-webserver is terminated by CTRL-C, suppress
        pass


def host_dagster_ui_with_workspace_process_context(
    workspace_process_context: IWorkspaceProcessContext,
    host: Optional[str],
    port: Optional[int],
    path_prefix: str,
    log_level: str,
):
    check.inst_param(
        workspace_process_context, "workspace_process_context", IWorkspaceProcessContext
    )
    host = check.opt_str_param(host, "host", "127.0.0.1")
    check.opt_int_param(port, "port")
    check.str_param(path_prefix, "path_prefix")

    logger = logging.getLogger(WEBSERVER_LOGGER_NAME)

    app = create_app_from_workspace_process_context(
        workspace_process_context, path_prefix, lifespan=_lifespan
    )

    if not port:
        if is_port_in_use(host, DEFAULT_WEBSERVER_PORT):
            port = find_free_port()
            logger.warning(f"Port {DEFAULT_WEBSERVER_PORT} is in use - using port {port} instead")
        else:
            port = DEFAULT_WEBSERVER_PORT

    logger.info(
        "Serving dagster-webserver on http://{host}:{port}{path_prefix} in process {pid}".format(
            host=host, port=port, path_prefix=path_prefix, pid=os.getpid()
        )
    )
    log_action(workspace_process_context.instance, START_DAGSTER_WEBSERVER)
    with uploading_logging_thread():
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level=log_level,
        )


cli = create_dagster_webserver_cli()


def main():
    # We only ever update this variable here. It is used to set the logger name as "dagit" if the
    # user invokes "dagit" on the command line.
    global WEBSERVER_LOGGER_NAME  # noqa: PLW0603

    # Click does not support passing multiple env var prefixes, so for backcompat we will convert any
    # DAGIT_* env vars to their DAGSTER_WEBSERVER_* equivalents here. Remove this in 2.0.
    for key, val in os.environ.items():
        if key.startswith("DAGIT_"):
            new_key = "DAGSTER_WEBSERVER_" + key[6:]
            if new_key not in os.environ:
                os.environ[new_key] = val

    if sys.argv[0].endswith("dagit"):
        WEBSERVER_LOGGER_NAME = "dagit"

    # click magic
    cli(auto_envvar_prefix="DAGSTER_WEBSERVER")
