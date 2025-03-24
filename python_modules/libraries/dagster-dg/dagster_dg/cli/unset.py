from pathlib import Path

import click
from dagster_shared import check

from dagster_dg.cli.shared_options import dg_global_options
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.env import Env
from dagster_dg.utils import DgClickCommand, DgClickGroup


@click.group(name="unset", cls=DgClickGroup)
def unset_group():
    """Commands for unsetting Dagster entities."""


# ########################
# ##### ENVIRONMENT
# ########################


@unset_group.command(name="env", cls=DgClickCommand)
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
