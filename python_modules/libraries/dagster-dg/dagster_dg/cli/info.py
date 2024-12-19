import json
import sys
from pathlib import Path
from typing import Any, Mapping

import click

from dagster_dg.context import (
    CodeLocationDirectoryContext,
    DgContext,
    is_inside_code_location_directory,
)
from dagster_dg.utils import DgClickCommand, DgClickGroup


@click.group(name="info", cls=DgClickGroup)
def info_cli():
    """Commands for listing Dagster components and related entities."""


def _serialize_json_schema(schema: Mapping[str, Any]) -> str:
    return json.dumps(schema, indent=4)


@info_cli.command(name="component-type", cls=DgClickCommand)
@click.argument("component_type", type=str)
@click.option("--description", is_flag=True, default=False)
@click.option("--generate-params-schema", is_flag=True, default=False)
@click.option("--component-params-schema", is_flag=True, default=False)
@click.pass_context
def info_component_type_command(
    cli_context: click.Context,
    component_type: str,
    description: bool,
    generate_params_schema: bool,
    component_params_schema: bool,
) -> None:
    """Get detailed information on a registered Dagster component type."""
    dg_context = DgContext.from_cli_context(cli_context)
    if not is_inside_code_location_directory(Path.cwd()):
        click.echo(
            click.style(
                "This command must be run inside a Dagster code location directory.", fg="red"
            )
        )
        sys.exit(1)

    context = CodeLocationDirectoryContext.from_path(Path.cwd(), dg_context)
    if not context.has_component_type(component_type):
        click.echo(
            click.style(f"No component type `{component_type}` could be resolved.", fg="red")
        )
        sys.exit(1)

    if sum([description, generate_params_schema, component_params_schema]) > 1:
        click.echo(
            click.style(
                "Only one of --description, --generate-params-schema, and --component-params-schema can be specified.",
                fg="red",
            )
        )
        sys.exit(1)

    component_type_metadata = context.get_component_type(component_type)

    if description:
        if component_type_metadata.description:
            click.echo(component_type_metadata.description)
        else:
            click.echo("No description available.")
    elif generate_params_schema:
        if component_type_metadata.generate_params_schema:
            click.echo(_serialize_json_schema(component_type_metadata.generate_params_schema))
        else:
            click.echo("No generate params schema defined.")
    elif component_params_schema:
        if component_type_metadata.component_params_schema:
            click.echo(_serialize_json_schema(component_type_metadata.component_params_schema))
        else:
            click.echo("No component params schema defined.")

    # print all available metadata
    else:
        click.echo(component_type)
        if component_type_metadata.description:
            click.echo("\nDescription:\n")
            click.echo(component_type_metadata.description)
        if component_type_metadata.generate_params_schema:
            click.echo("\nGenerate params schema:\n")
            click.echo(_serialize_json_schema(component_type_metadata.generate_params_schema))
        if component_type_metadata.component_params_schema:
            click.echo("\nComponent params schema:\n")
            click.echo(_serialize_json_schema(component_type_metadata.component_params_schema))
