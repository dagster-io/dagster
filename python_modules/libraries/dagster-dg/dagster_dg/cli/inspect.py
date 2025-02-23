import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import click

from dagster_dg.cli.global_options import dg_global_options
from dagster_dg.component import RemoteComponentRegistry
from dagster_dg.component_key import GlobalComponentKey
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.utils import (
    DgClickCommand,
    DgClickGroup,
    exit_with_error,
    generate_missing_component_type_error_message,
)


@click.group(name="inspect", cls=DgClickGroup)
def inspect_group():
    """Commands for inspecting Dagster entities."""


# ########################
# ##### COMPONENT TYPE
# ########################


@inspect_group.command(name="component-type", cls=DgClickCommand)
@click.argument("component_type", type=str)
@click.option("--description", is_flag=True, default=False)
@click.option("--scaffold-params-schema", is_flag=True, default=False)
@click.option("--component-schema", is_flag=True, default=False)
@dg_global_options
@click.pass_context
def component_type_inspect_command(
    context: click.Context,
    component_type: str,
    description: bool,
    scaffold_params_schema: bool,
    component_schema: bool,
    **global_options: object,
) -> None:
    """Get detailed information on a registered Dagster component type."""
    cli_config = normalize_cli_config(global_options, context)
    dg_context = DgContext.for_defined_registry_environment(Path.cwd(), cli_config)
    registry = RemoteComponentRegistry.from_dg_context(dg_context)
    component_key = GlobalComponentKey.from_typename(component_type)
    if not registry.has_global(component_key):
        exit_with_error(generate_missing_component_type_error_message(component_type))
    elif sum([description, scaffold_params_schema, component_schema]) > 1:
        exit_with_error(
            "Only one of --description, --scaffold-params-schema, and --component-schema can be specified."
        )

    component_type_metadata = registry.get_global(component_key)

    if description:
        if component_type_metadata.description:
            click.echo(component_type_metadata.description)
        else:
            click.echo("No description available.")
    elif scaffold_params_schema:
        if component_type_metadata.scaffold_params_schema:
            click.echo(_serialize_json_schema(component_type_metadata.scaffold_params_schema))
        else:
            click.echo("No scaffold params schema defined.")
    elif component_schema:
        if component_type_metadata.component_schema:
            click.echo(_serialize_json_schema(component_type_metadata.component_schema))
        else:
            click.echo("No component schema defined.")

    # print all available metadata
    else:
        click.echo(component_type)
        if component_type_metadata.description:
            click.echo("\nDescription:\n")
            click.echo(component_type_metadata.description)
        if component_type_metadata.scaffold_params_schema:
            click.echo("\nScaffold params schema:\n")
            click.echo(_serialize_json_schema(component_type_metadata.scaffold_params_schema))
        if component_type_metadata.component_schema:
            click.echo("\nComponent schema:\n")
            click.echo(_serialize_json_schema(component_type_metadata.component_schema))


def _serialize_json_schema(schema: Mapping[str, Any]) -> str:
    return json.dumps(schema, indent=4)
