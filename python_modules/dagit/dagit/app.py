from starlette.applications import Starlette

from dagster import DagsterInstance
from dagster import _check as check
from dagster.cli.workspace.cli_target import get_workspace_process_context_from_kwargs
from dagster.core.execution.compute_logs import warn_if_compute_logs_disabled
from dagster.core.telemetry import log_workspace_stats
from dagster.core.workspace.context import WorkspaceProcessContext

from .version import __version__
from .webserver import DagitWebserver


def create_app_from_workspace_process_context(
    workspace_process_context: WorkspaceProcessContext,
    path_prefix: str = "",
) -> Starlette:
    check.inst_param(
        workspace_process_context, "workspace_process_context", WorkspaceProcessContext
    )
    check.str_param(path_prefix, "path_prefix")

    instance = workspace_process_context.instance

    if path_prefix:
        if not path_prefix.startswith("/"):
            raise Exception(f'The path prefix should begin with a leading "/": got {path_prefix}')
        if path_prefix.endswith("/"):
            raise Exception(f'The path prefix should not include a trailing "/": got {path_prefix}')

    warn_if_compute_logs_disabled()

    log_workspace_stats(instance, workspace_process_context)

    return DagitWebserver(
        workspace_process_context,
        path_prefix,
    ).create_asgi_app()


def default_app(debug=False):
    instance = DagsterInstance.get()
    process_context = get_workspace_process_context_from_kwargs(
        instance=instance,
        version=__version__,
        read_only=False,
        kwargs={},
    )

    return DagitWebserver(
        process_context,
    ).create_asgi_app(debug=debug)


def debug_app():
    return default_app(debug=True)
