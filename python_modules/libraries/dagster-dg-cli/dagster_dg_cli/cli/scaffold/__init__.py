"""Scaffold submodule for dagster-dg CLI."""

import click
from dagster_dg_core.utils import DgClickGroup

from dagster_dg_cli.cli.scaffold.branch.command import scaffold_branch_command
from dagster_dg_cli.cli.scaffold.build_artifacts import scaffold_build_artifacts_command
from dagster_dg_cli.cli.scaffold.component import scaffold_component_command
from dagster_dg_cli.cli.scaffold.defs import scaffold_defs_group
from dagster_dg_cli.cli.scaffold.github_actions import scaffold_github_actions_command


@click.group(name="scaffold", cls=DgClickGroup)
def scaffold_group():
    """Commands for scaffolding Dagster entities."""


# Register all scaffold commands from submodules
scaffold_group.add_command(scaffold_branch_command)
scaffold_group.add_command(scaffold_build_artifacts_command)  # Legacy shim
scaffold_group.add_command(scaffold_component_command)
scaffold_group.add_command(scaffold_defs_group)
scaffold_group.add_command(scaffold_github_actions_command)  # Legacy shim
