import json
import sys
from pathlib import Path
from typing import Any, Mapping

import click

from dagster_dg.cli.global_options import dg_global_options
from dagster_dg.context import (
    CodeLocationDirectoryContext,
    DgContext,
    is_inside_code_location_directory,
)
from dagster_dg.generate import generate_component_type
from dagster_dg.utils import DgClickCommand, DgClickGroup


@click.group(name="component-type", cls=DgClickGroup)
def component_type_group():
    """Commands for operating on components types."""


# ########################
# ##### GENERATE
# ########################


@component_type_group.command(name="generate", cls=DgClickCommand)
@click.argument("name", type=str)
@dg_global_options
def component_type_generate_command(name: str, **global_options: object) -> None:
    """Generate a scaffold of a custom Dagster component type.

    This command must be run inside a Dagster code location directory. The component type scaffold
    will be generated in submodule `<code_location_name>.lib.<name>`.
    """
    dg_context = DgContext.from_cli_global_options(global_options)
    if not is_inside_code_location_directory(Path.cwd()):
        click.echo(
            click.style(
                "This command must be run inside a Dagster code location directory.", fg="red"
            )
        )
        sys.exit(1)
    context = CodeLocationDirectoryContext.from_path(Path.cwd(), dg_context)
    full_component_name = f"{context.name}.{name}"
    if context.has_component_type(full_component_name):
        click.echo(click.style(f"A component type named `{name}` already exists.", fg="red"))
        sys.exit(1)

    generate_component_type(context, name)


# ########################
# ##### INFO
# ########################


@component_type_group.command(name="info", cls=DgClickCommand)
@click.argument("component_type", type=str)
@click.option("--description", is_flag=True, default=False)
@click.option("--generate-params-schema", is_flag=True, default=False)
@click.option("--component-params-schema", is_flag=True, default=False)
@dg_global_options
def component_type_info_command(
    component_type: str,
    description: bool,
    generate_params_schema: bool,
    component_params_schema: bool,
    **global_options: object,
) -> None:
    """Get detailed information on a registered Dagster component type."""
    dg_context = DgContext.from_cli_global_options(global_options)
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


def _serialize_json_schema(schema: Mapping[str, Any]) -> str:
    return json.dumps(schema, indent=4)


# ########################
# ##### LIST
# ########################


@component_type_group.command(name="list", cls=DgClickCommand)
@dg_global_options
def component_type_list(**global_options: object) -> None:
    """List registered Dagster components in the current code location environment."""
    dg_context = DgContext.from_cli_global_options(global_options)
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
