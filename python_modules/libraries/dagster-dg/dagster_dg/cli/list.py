import sys
from pathlib import Path

import click

from dagster_dg.context import (
    CodeLocationProjectContext,
    DeploymentProjectContext,
    is_inside_code_location_project,
    is_inside_deployment_project,
)


@click.group(name="list")
def list_cli():
    """Commands for listing Dagster components and related entities."""


@list_cli.command(name="code-locations")
def list_code_locations_command() -> None:
    """List code locations in the current deployment."""
    if not is_inside_deployment_project(Path.cwd()):
        click.echo(
            click.style("This command must be run inside a Dagster deployment directory.", fg="red")
        )
        sys.exit(1)

    context = DeploymentProjectContext.from_path(Path.cwd())
    for code_location in context.list_code_locations():
        click.echo(code_location)


@list_cli.command(name="component-types")
def list_component_types_command() -> None:
    """List registered Dagster components in the current code location environment."""
    if not is_inside_code_location_project(Path.cwd()):
        click.echo(
            click.style(
                "This command must be run inside a Dagster code location directory.", fg="red"
            )
        )
        sys.exit(1)

    context = CodeLocationProjectContext.from_path(Path.cwd())
    for component_type in context.list_component_types():
        click.echo(component_type)


@list_cli.command(name="components")
def list_components_command() -> None:
    """List Dagster component instances defined in the current code location."""
    if not is_inside_code_location_project(Path.cwd()):
        click.echo(
            click.style(
                "This command must be run inside a Dagster code location directory.", fg="red"
            )
        )
        sys.exit(1)

    context = CodeLocationProjectContext.from_path(Path.cwd())
    for component_name in context.component_instances:
        click.echo(component_name)
