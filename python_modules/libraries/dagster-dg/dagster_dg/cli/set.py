from pathlib import Path
from typing import Optional

import click
from dagster_shared import check

from dagster_dg.cli.shared_options import dg_global_options
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.env import Env
from dagster_dg.utils import DgClickCommand, DgClickGroup


@click.group(name="set", cls=DgClickGroup)
def set_group():
    """Commands for setting Dagster entities."""


# ########################
# ##### ENVIRONMENT
# ########################


@set_group.command(name="env", cls=DgClickCommand)
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
