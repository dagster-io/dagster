from pathlib import Path
from typing import Optional

import click
from dagster_shared import check
from rich.console import Console
from rich.table import Table

from dagster_dg.cli.shared_options import dg_global_options
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.env import Env
from dagster_dg.utils import DgClickCommand, DgClickGroup


@click.group(name="env", cls=DgClickGroup)
def env_group():
    """Commands for managing environment variables."""


# ########################
# ##### ENVIRONMENT
# ########################


@env_group.command(name="list", cls=DgClickCommand)
@dg_global_options
def list_env_command(**global_options: object) -> None:
    """List environment variables defined in the current project."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_project_environment(Path.cwd(), cli_config)

    env = Env.from_ctx(dg_context)
    if not env.values:
        click.echo("No environment variables are defined for this project.")
        return

    table = Table(border_style="dim")
    table.add_column("Env Var")
    table.add_column("Value")
    for key, value in env.values.items():
        table.add_row(key, value)
    console = Console()
    console.print(table)


# ########################
# ##### SET UNSET
# ########################


@env_group.command(name="set", cls=DgClickCommand)
@click.argument("key", type=str)
@click.argument("value", type=str, required=False)
@dg_global_options
def set_env_command(key: str, value: Optional[str], **global_options: object) -> None:
    """Set environment variables for the current project."""
    check.invariant(
        value is not None or "=" in key,
        "Input must be of the form `dg set env KEY=VALUE` or `dg set env KEY VALUE`",
    )
    if "=" in key:
        key, value = key.split("=", 1)
    else:
        value = None

    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_project_environment(Path.cwd(), cli_config)

    env = Env.from_ctx(dg_context).with_values({key: value})
    env.write()


@env_group.command(name="unset", cls=DgClickCommand)
@click.argument("key", type=str)
@dg_global_options
def unset_env_command(key: str, **global_options: object) -> None:
    """Unset environment variable for the current project."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_project_environment(Path.cwd(), cli_config)

    check.invariant(
        key in Env.from_ctx(dg_context).values,
        f"Environment variable {key} is not set.",
    )

    env = Env.from_ctx(dg_context).without_values({key})
    env.write()
