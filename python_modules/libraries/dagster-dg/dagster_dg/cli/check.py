import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import click

from dagster_dg.check import check_yaml as check_yaml_fn
from dagster_dg.cli.dev import format_forwarded_option
from dagster_dg.cli.shared_options import dg_global_options
from dagster_dg.cli.utils import create_dagster_cli_cmd
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.utils import DgClickCommand, DgClickGroup, pushd
from dagster_dg.utils.filesystem import watch_paths
from dagster_dg.utils.telemetry import cli_telemetry_wrapper


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
@dg_global_options
@cli_telemetry_wrapper
def check_yaml_command(
    paths: Sequence[str],
    watch: bool,
    **global_options: object,
) -> None:
    """Check component.yaml files against their schemas, showing validation errors."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_project_environment(Path.cwd(), cli_config)
    resolved_paths = [Path(path).absolute() for path in paths]

    def run_check(_: Any = None) -> bool:
        return check_yaml_fn(dg_context, resolved_paths)

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
    default=True,
    help="Whether to schema-check component.yaml files for the project before loading and checking all definitions.",
)
@dg_global_options
@click.pass_context
@cli_telemetry_wrapper
def check_definitions_command(
    context: click.Context,
    log_level: str,
    log_format: str,
    verbose: bool,
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
    cli_config = normalize_cli_config(global_options, context)
    dg_context = DgContext.for_workspace_or_project_environment(Path.cwd(), cli_config)

    forward_options = [
        *format_forwarded_option("--log-level", log_level),
        *format_forwarded_option("--log-format", log_format),
        *(["--verbose"] if verbose else []),
    ]

    if dg_context.use_dg_managed_environment:
        run_cmds = ["uv", "run", "dagster", "definitions", "validate"]
    elif dg_context.is_project:
        run_cmds = ["dagster", "definitions", "validate"]
    else:
        run_cmds = ["uv", "tool", "run", "dagster", "definitions", "validate"]

    with (
        pushd(dg_context.root_path),
        create_dagster_cli_cmd(dg_context, forward_options, run_cmds) as (
            cmd_location,
            cmd,
            workspace_file,
        ),
    ):
        if check_yaml_fn:
            overall_check_result = True
            project_dirs = (
                [project.path for project in dg_context.project_specs]
                if dg_context.is_workspace
                else [dg_context.root_path]
            )
            for project_dir in project_dirs:
                check_result = check_yaml_fn(
                    dg_context.for_project_environment(project_dir, cli_config),
                    [],
                )
                overall_check_result = overall_check_result and check_result
            if not overall_check_result:
                click.get_current_context().exit(1)
        print(f"Using {cmd_location}")  # noqa: T201
        if workspace_file:  # only non-None deployment context
            cmd.extend(["--workspace", workspace_file])

        print(" ".join(cmd))  # noqa: T201

        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            sys.exit(result.returncode)

    click.echo("All definitions loaded successfully.")
