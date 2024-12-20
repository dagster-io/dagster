import os
import sys
from pathlib import Path

import click

from dagster_dg.generate import generate_deployment
from dagster_dg.utils import DgClickCommand, DgClickGroup


@click.group(name="deployment", cls=DgClickGroup)
def deployment_group():
    """Commands for operating on deployment directories."""


# ########################
# ##### GENERATE
# ########################


@deployment_group.command(name="generate", cls=DgClickCommand)
@click.argument("path", type=Path)
def deployment_generate_command(path: Path) -> None:
    """Generate a Dagster deployment file structure.

    The deployment file structure includes a directory for code locations and configuration files
    for deploying to Dagster Plus.
    """
    dir_abspath = os.path.abspath(path)
    if os.path.exists(dir_abspath):
        click.echo(
            click.style(f"A file or directory at {dir_abspath} already exists. ", fg="red")
            + "\nPlease delete the contents of this path or choose another location."
        )
        sys.exit(1)
    generate_deployment(path)
