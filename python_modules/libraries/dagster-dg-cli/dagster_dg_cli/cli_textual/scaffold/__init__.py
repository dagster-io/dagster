"""Scaffold submodule for dg-web CLI."""

import click
from dagster_dg_core.utils import DgClickGroup

from dagster_dg_cli.cli_textual.scaffold.branch import scaffold_branch_command


@click.group(name="scaffold", cls=DgClickGroup)
def scaffold_group():
    """Commands for scaffolding Dagster entities using Textual interface."""


# Register scaffold commands
scaffold_group.add_command(scaffold_branch_command)

__all__ = [
    "scaffold_branch_command",
    "scaffold_group",
]
