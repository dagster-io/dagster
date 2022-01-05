from dagster import check
from dagster.core.execution.compute_logs import warn_if_compute_logs_disabled
from dagster.core.telemetry import log_workspace_stats
from dagster.core.workspace.context import WorkspaceProcessContext
from starlette.applications import Starlette

from .starlette import DagitWebserver


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
