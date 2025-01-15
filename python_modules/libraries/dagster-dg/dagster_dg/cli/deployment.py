import os
from pathlib import Path

import click

from dagster_dg.cli.global_options import dg_global_options
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.scaffold import scaffold_deployment
from dagster_dg.utils import DgClickCommand, DgClickGroup, exit_with_error


@click.group(name="deployment", cls=DgClickGroup)
def deployment_group():
    """Commands for operating on deployment directories."""


# ########################
# ##### SCAFFOLD
# ########################


@deployment_group.command(name="scaffold", cls=DgClickCommand)
@dg_global_options
@click.argument("path", type=Path)
@click.pass_context
def deployment_scaffold_command(
    context: click.Context, path: Path, **global_options: object
) -> None:
    """Scaffold a Dagster deployment file structure.

    The deployment file structure includes a directory for code locations and configuration files
    for deploying to Dagster Plus.
    """
    cli_config = normalize_cli_config(global_options, context)
    dg_context = DgContext.from_config_file_discovery_and_cli_config(Path.cwd(), cli_config)
    dir_abspath = os.path.abspath(path)
    if os.path.exists(dir_abspath):
        exit_with_error(
            f"A file or directory at {dir_abspath} already exists. "
            + "\nPlease delete the contents of this path or choose another location."
        )
    scaffold_deployment(path, dg_context)
