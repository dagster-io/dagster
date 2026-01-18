import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Optional, TypeVar

import click
from dagster_dg_core.config import normalize_cli_config
from dagster_dg_core.context import DgContext
from dagster_dg_core.shared_options import dg_global_options, dg_path_options, dg_venv_options
from dagster_dg_core.utils import DgClickCommand, exit_with_error, pushd
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.cli import WorkspaceOpts, dg_workspace_options

from dagster_dg_cli.cli.utils import create_temp_workspace_file

T = TypeVar("T")


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
    help="Whether to schema-check defs.yaml files for the project before starting the dev server.",
    default=None,
)
@dg_path_options
@dg_global_options
@dg_venv_options
@dg_workspace_options
@cli_telemetry_wrapper
def dev_command(
    code_server_log_level: str,
    log_level: str,
    log_format: str,
    port: Optional[int],
    host: Optional[str],
    live_data_poll_rate: int,
    check_yaml: Optional[bool],
    target_path: Path,
    verbose: bool,  # from dg_global_options
    use_active_venv: bool,
    **other_options: Mapping[str, object],
) -> None:
    """Start a local instance of Dagster.

    If run inside a workspace directory, this command will launch all projects in the
    workspace. If launched inside a project directory, it will launch only that project.
    """
    from dagster_dg_core.check import check_yaml as check_yaml_fn

    workspace_opts = WorkspaceOpts.extract_from_cli_options(other_options)

    # If we got CLI flags that specify a target jump right to dagster core
    if workspace_opts.specifies_target():
        from dagster._cli.dev import dev_command_impl

        return dev_command_impl(
            code_server_log_level=code_server_log_level,
            log_level=log_level,
            log_format=log_format,
            port=str(port) if port else None,
            host=host,
            live_data_poll_rate=str(live_data_poll_rate),
            use_legacy_code_server_behavior=False,
            shutdown_pipe=None,
            verbose=verbose,
            workspace_opts=workspace_opts,
        )

    # If not, use dg config to construct a workspace file and do a yaml check before
    # invoking dagster core
    cli_config = normalize_cli_config(other_options, click.get_current_context())
    dg_context = DgContext.for_workspace_or_project_environment(target_path, cli_config)

    if dg_context.is_project:
        os.environ["DAGSTER_PROJECT_ENV_FILE_PATHS"] = json.dumps(
            {dg_context.code_location_name: str(dg_context.root_path)}
        )
        if check_yaml is None:
            # default to checking yaml in a project context
            check_yaml = True
    else:
        os.environ["DAGSTER_PROJECT_ENV_FILE_PATHS"] = json.dumps(
            {
                dg_context.with_root_path(
                    dg_context.workspace_root_path / project.path
                ).code_location_name: str(project.path)
                for project in dg_context.project_specs
            }
        )
        if check_yaml is True:
            exit_with_error("--check-yaml is not currently supported in a workspace context")
        check_yaml = False

    with (
        pushd(dg_context.root_path),
        create_temp_workspace_file(dg_context, use_active_venv) as workspace_file,
    ):
        if check_yaml:
            overall_check_result = True
            project_dirs = (
                [dg_context.root_path]
                if dg_context.is_project
                else [project.path for project in dg_context.project_specs]
            )
            for project_dir in project_dirs:
                check_result = check_yaml_fn(
                    dg_context.for_project_environment(project_dir, cli_config),
                    [],
                    validate_requirements=False,
                )
                overall_check_result = overall_check_result and check_result
            if not overall_check_result:
                click.get_current_context().exit(1)

        from dagster._cli.dev import dev_command_impl

        dev_command_impl(
            code_server_log_level=code_server_log_level,
            log_level=log_level,
            log_format=log_format,
            port=str(port) if port else None,
            host=host,
            live_data_poll_rate=str(live_data_poll_rate),
            use_legacy_code_server_behavior=False,
            shutdown_pipe=None,
            verbose=verbose,
            workspace_opts=WorkspaceOpts(workspace=[workspace_file]),
        )
