from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from dagster_dg.cli.shared_options import dg_global_options
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.env import ProjectEnvVars
from dagster_dg.utils import DgClickCommand, DgClickGroup
from dagster_dg.utils.telemetry import cli_telemetry_wrapper


@click.group(name="env", cls=DgClickGroup)
def env_group():
    """Commands for managing environment variables."""


# ########################
# ##### ENVIRONMENT
# ########################


@env_group.command(name="list", cls=DgClickCommand)
@dg_global_options
@cli_telemetry_wrapper
def list_env_command(**global_options: object) -> None:
    """List environment variables from the .env file of the current project."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_project_environment(Path.cwd(), cli_config)

    env = ProjectEnvVars.from_ctx(dg_context)
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
