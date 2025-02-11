from collections import defaultdict
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from yaml.scanner import ScannerError

from dagster_dg.cli.global_options import dg_global_options
from dagster_dg.component import get_specified_env_var_deps
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.env import Env
from dagster_dg.utils import DgClickCommand, DgClickGroup
from dagster_dg.yaml_utils import parse_yaml_with_source_positions


@click.group(name="env", cls=DgClickGroup)
def env_group():
    """Commands for operating on a code location's environment."""


# ########################
# ##### MANAGE ENV
# ########################


def get_used_env_vars_for_components(dg_context: DgContext) -> dict[str, set[str]]:
    component_usage_by_env_var: dict[str, set[str]] = defaultdict(set)

    for component_dir in dg_context.components_path.iterdir():
        component_path = component_dir / "component.yaml"

        if component_path.exists():
            text = component_path.read_text()
            try:
                component_doc_tree = parse_yaml_with_source_positions(
                    text, filename=str(component_path)
                )
                specified_env_var_deps = get_specified_env_var_deps(component_doc_tree.value)
                for env_var in specified_env_var_deps:
                    component_usage_by_env_var[env_var].add(component_dir.name)

            except ScannerError:
                pass

    return component_usage_by_env_var


@env_group.command(name="list", cls=DgClickCommand)
@dg_global_options
@click.option("--verbose", is_flag=True, default=False)
@click.pass_context
def env_list_command(context: click.Context, verbose: bool, **global_options: object) -> None:
    """List the environment variables for the current code location.

    This command must be run inside a Dagster code location directory.
    """
    cli_config = normalize_cli_config(global_options, context)
    dg_context = DgContext.for_code_location_environment(Path.cwd(), cli_config)

    env = Env.from_file(dg_context.env_file, dg_context.deployment_env_file)
    used_env_vars = get_used_env_vars_for_components(dg_context)

    table = Table(border_style="dim")
    table.add_column("Scope", style="bold red")
    table.add_column("Env Var", style="bold cyan", no_wrap=True)
    table.add_column("Value")
    table.add_column("Uses")
    for env_var, value in env.deployment_values.items():
        if env_var in env.code_location_values:
            continue

        users = list(used_env_vars[env_var])
        users_string = ", ".join(users)
        if not verbose and len(users) > 2:
            users_string = ", ".join(users[:2]) + "..."

        users = f"{len(used_env_vars[env_var])}" + (f" ({users_string})" if users else "")
        table.add_row("deployment", env_var, value, users)
    for env_var, value in env.code_location_values.items():
        users = list(used_env_vars[env_var])
        users_string = ", ".join(users)
        if not verbose and len(users) > 2:
            users_string = ", ".join(users[:2]) + "..."

        users = f"{len(used_env_vars[env_var])}" + (f" ({users_string})" if users else "")
        table.add_row("code location", env_var, value, users)
    console = Console()
    console.print(table)


@env_group.command(name="set", cls=DgClickCommand)
@dg_global_options
@click.argument("key")
@click.argument("value", required=False)
@click.option("--deployment", is_flag=True, default=False)
@click.pass_context
def env_set_command(
    context: click.Context, key: str, value: str, deployment: bool, **global_options: object
) -> None:
    """Set an environment variable for the current code location."""
    assert ("=" not in key or value is None) and (
        value is not None or "=" in key
    ), "Input must be in the format `dg env get KEY=value` or `dg env set KEY value`"

    if "=" in key:
        key, value = key.split("=", 1)

    cli_config = normalize_cli_config(global_options, context)
    dg_context = DgContext.for_code_location_environment(Path.cwd(), cli_config)

    env = Env.from_file(dg_context.env_file, dg_context.deployment_env_file)

    if deployment:
        env.set_deployment_value(key, value)
    else:
        env.set_code_location_value(key, value)


@env_group.command(name="unset", cls=DgClickCommand)
@dg_global_options
@click.argument("key")
@click.option("--deployment", is_flag=True, default=False)
@click.pass_context
def env_unset_command(
    context: click.Context, key: str, deployment: bool, **global_options: object
) -> None:
    """Unset an environment variable for the current code location."""
    cli_config = normalize_cli_config(global_options, context)
    dg_context = DgContext.for_code_location_environment(Path.cwd(), cli_config)

    env = Env.from_file(dg_context.env_file, dg_context.deployment_env_file)
    if deployment:
        env.unset_deployment_value(key)
    else:
        env.unset_code_location_value(key)
