import sys
from pathlib import Path

import click

from dagster_dg.context import (
    CodeLocationDirectoryContext,
    DeploymentDirectoryContext,
    is_inside_code_location_directory,
    is_inside_deployment_directory,
)


@click.group(name="list")
def list_cli():
    """Commands for listing Dagster components and related entities."""


@list_cli.command(name="code-locations")
def list_code_locations_command() -> None:
    """List code locations in the current deployment."""
    if not is_inside_deployment_directory(Path.cwd()):
        click.echo(
            click.style("This command must be run inside a Dagster deployment directory.", fg="red")
        )
        sys.exit(1)

    context = DeploymentDirectoryContext.from_path(Path.cwd())
    for code_location in context.get_code_location_names():
        click.echo(code_location)


@list_cli.command(name="component-types")
def list_component_types_command() -> None:
    """List registered Dagster components in the current code location environment."""
    if not is_inside_code_location_directory(Path.cwd()):
        click.echo(
            click.style(
                "This command must be run inside a Dagster code location directory.", fg="red"
            )
        )
        sys.exit(1)

    context = CodeLocationDirectoryContext.from_path(Path.cwd())
    for key, component_type in context.iter_component_types():
        click.echo(key)
        if component_type.summary:
            click.echo(f"    {component_type.summary}")


@list_cli.command(name="components")
def list_components_command() -> None:
    """List Dagster component instances defined in the current code location."""
    if not is_inside_code_location_directory(Path.cwd()):
        click.echo(
            click.style(
                "This command must be run inside a Dagster code location directory.", fg="red"
            )
        )
        sys.exit(1)

    context = CodeLocationDirectoryContext.from_path(Path.cwd())
    for component_name in context.get_component_instance_names():
        click.echo(component_name)
