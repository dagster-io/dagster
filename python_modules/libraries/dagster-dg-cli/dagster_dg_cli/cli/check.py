from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Optional

import click
from dagster_dg_core.config import normalize_cli_config
from dagster_dg_core.context import DgContext
from dagster_dg_core.shared_options import dg_global_options, dg_path_options
from dagster_dg_core.utils import DgClickCommand, DgClickGroup, exit_with_error, pushd
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper

from dagster_dg_cli.cli.utils import create_temp_workspace_file


@click.group(name="check", cls=DgClickGroup)
def check_group():
    """Commands for checking the integrity of your Dagster code."""


# ########################
# ##### COMPONENT
# ########################


@check_group.command(name="yaml", cls=DgClickCommand)
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option(
    "--watch", is_flag=True, help="Watch for changes to the component files and re-validate them."
)
@click.option(
    "--validate-requirements",
    "--no-validate-requirements",
    is_flag=True,
    default=True,
    help="Validate environment variables in requirements for all components in the given module.",
)
@dg_global_options
@dg_path_options
@cli_telemetry_wrapper
def check_yaml_command(
    paths: Sequence[str],
    watch: bool,
    validate_requirements: bool,
    target_path: Path,
    **global_options: object,
) -> None:
    """Check defs.yaml files against their schemas, showing validation errors."""
    from dagster_dg_core.utils.filesystem import watch_paths

    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_project_environment(target_path, cli_config)
    resolved_paths = [Path(p).absolute() for p in paths]

    def run_check(_: Any = None) -> bool:
        # defer for import performance
        from dagster_dg_core.check import check_yaml as check_yaml_fn

        return check_yaml_fn(dg_context, resolved_paths, validate_requirements)

    if watch:
        watched_paths = (
            resolved_paths or [dg_context.defs_path]
        ) + dg_context.component_registry_paths()
        watch_paths(watched_paths, run_check)
    else:
        if run_check(None):
            click.get_current_context().exit(0)
        else:
            click.get_current_context().exit(1)


@check_group.command(name="defs", cls=DgClickCommand)
@click.option(
    "--log-level",
    help="Set the log level for dagster services.",
    show_default=True,
    default="warning",
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
    "--verbose",
    "-v",
    flag_value=True,
    default=False,
    help="Show verbose error messages, including system frames in stack traces.",
)
@click.option(
    "--check-yaml/--no-check-yaml",
    flag_value=True,
    help="Whether to schema-check defs.yaml files for the project before loading and checking all definitions.",
    default=None,
)
@dg_path_options
@dg_global_options
@click.pass_context
@cli_telemetry_wrapper
def check_definitions_command(
    context: click.Context,
    log_level: str,
    log_format: str,
    verbose: bool,
    target_path: Path,
    check_yaml: Optional[bool],
    **global_options: Mapping[str, object],
) -> None:
    """Loads and validates your Dagster definitions using a Dagster instance.

    If run inside a deployment directory, this command will launch all code locations in the
    deployment. If launched inside a code location directory, it will launch only that code
    location.

    When running, this command sets the environment variable `DAGSTER_IS_DEFS_VALIDATION_CLI=1`.
    This environment variable can be used to control the behavior of your code in validation mode.

    This command returns an exit code 1 when errors are found, otherwise an exit code 0.

    """
    # defer for import performance
    from dagster_dg_core.check import check_yaml as check_yaml_fn

    cli_config = normalize_cli_config(global_options, context)
    dg_context = DgContext.for_workspace_or_project_environment(target_path, cli_config)

    if check_yaml is True and not dg_context.is_project:
        exit_with_error("--check-yaml is not currently supported in a workspace context")

    if check_yaml is None:
        check_yaml = dg_context.is_project

    with (
        pushd(dg_context.root_path),
        create_temp_workspace_file(dg_context) as workspace_file,
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

        from dagster._cli.definitions import definitions_validate_command_impl

        definitions_validate_command_impl(
            log_level=log_level,
            log_format=log_format,
            allow_in_process=True,
            verbose=verbose,
            workspace=[workspace_file],
        )

    click.echo("All definitions loaded successfully.")
