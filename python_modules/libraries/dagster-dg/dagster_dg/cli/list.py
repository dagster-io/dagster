import sys
from pathlib import Path

import click

from dagster_dg.context import (
    CodeLocationDirectoryContext,
    DeploymentDirectoryContext,
    DgContext,
    is_inside_code_location_directory,
    is_inside_deployment_directory,
)
from dagster_dg.utils import DgClickCommand, DgClickGroup


@click.group(name="list", cls=DgClickGroup)
def list_cli():
    """Commands for listing Dagster components and related entities."""


@list_cli.command(name="code-locations", cls=DgClickCommand)
@click.pass_context
def list_code_locations_command(cli_context: click.Context) -> None:
    """List code locations in the current deployment."""
    dg_context = DgContext.from_cli_context(cli_context)
    if not is_inside_deployment_directory(Path.cwd()):
        click.echo(
            click.style("This command must be run inside a Dagster deployment directory.", fg="red")
        )
        sys.exit(1)

    context = DeploymentDirectoryContext.from_path(Path.cwd(), dg_context)
    for code_location in context.get_code_location_names():
        click.echo(code_location)


@list_cli.command(name="component-types", cls=DgClickCommand)
@click.pass_context
def list_component_types_command(cli_context: click.Context) -> None:
    """List registered Dagster components in the current code location environment."""
    dg_context = DgContext.from_cli_context(cli_context)
    if not is_inside_code_location_directory(Path.cwd()):
        click.echo(
            click.style(
                "This command must be run inside a Dagster code location directory.", fg="red"
            )
        )
        sys.exit(1)

    context = CodeLocationDirectoryContext.from_path(Path.cwd(), dg_context)
    for key, component_type in context.iter_component_types():
        click.echo(key)
        if component_type.summary:
            click.echo(f"    {component_type.summary}")


@list_cli.command(name="components", cls=DgClickCommand)
@click.pass_context
def list_components_command(cli_context: click.Context) -> None:
    """List Dagster component instances defined in the current code location."""
    dg_context = DgContext.from_cli_context(cli_context)
    if not is_inside_code_location_directory(Path.cwd()):
        click.echo(
            click.style(
                "This command must be run inside a Dagster code location directory.", fg="red"
            )
        )
        sys.exit(1)

    context = CodeLocationDirectoryContext.from_path(Path.cwd(), dg_context)
    for component_name in context.get_component_instance_names():
        click.echo(component_name)
