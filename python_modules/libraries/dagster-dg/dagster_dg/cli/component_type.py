import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import click

from dagster_dg.cli.global_options import dg_global_options
from dagster_dg.component import RemoteComponentRegistry
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.docs import markdown_for_component_type, render_markdown_in_browser
from dagster_dg.scaffold import scaffold_component_type
from dagster_dg.utils import DgClickCommand, DgClickGroup, exit_with_error


@click.group(name="component-type", cls=DgClickGroup)
def component_type_group():
    """Commands for operating on components types."""


# ########################
# ##### SCAFFOLD
# ########################


@component_type_group.command(name="scaffold", cls=DgClickCommand)
@click.argument("name", type=str)
@dg_global_options
@click.pass_context
def component_type_scaffold_command(
    context: click.Context, name: str, **global_options: object
) -> None:
    """Scaffold of a custom Dagster component type.

    This command must be run inside a Dagster code location directory. The component type scaffold
    will be placed in submodule `<code_location_name>.lib.<name>`.
    """
    cli_config = normalize_cli_config(global_options, context)
    dg_context = DgContext.from_config_file_discovery_and_cli_config(Path.cwd(), cli_config)
    if not dg_context.is_code_location:
        exit_with_error("This command must be run inside a Dagster code location directory.")
    registry = RemoteComponentRegistry.from_dg_context(dg_context)
    full_component_name = f"{dg_context.root_package_name}.{name}"
    if registry.has(full_component_name):
        exit_with_error(f"A component type named `{name}` already exists.")

    scaffold_component_type(dg_context, name)


# ########################
# ##### DOCS
# ########################


@component_type_group.command(name="docs", cls=DgClickCommand)
@click.argument("component_type", type=str)
@dg_global_options
@click.pass_context
def component_type_docs_command(
    context: click.Context,
    component_type: str,
    **global_options: object,
) -> None:
    """Get detailed information on a registered Dagster component type."""
    cli_config = normalize_cli_config(global_options, context)
    dg_context = DgContext.from_config_file_discovery_and_cli_config(Path.cwd(), cli_config)
    registry = RemoteComponentRegistry.from_dg_context(dg_context)
    if not registry.has(component_type):
        exit_with_error(f"No component type `{component_type}` could be resolved.")

    render_markdown_in_browser(markdown_for_component_type(registry.get(component_type)))


# ########################
# ##### INFO
# ########################


@component_type_group.command(name="info", cls=DgClickCommand)
@click.argument("component_type", type=str)
@click.option("--description", is_flag=True, default=False)
@click.option("--scaffold-params-schema", is_flag=True, default=False)
@click.option("--component-params-schema", is_flag=True, default=False)
@dg_global_options
@click.pass_context
def component_type_info_command(
    context: click.Context,
    component_type: str,
    description: bool,
    scaffold_params_schema: bool,
    component_params_schema: bool,
    **global_options: object,
) -> None:
    """Get detailed information on a registered Dagster component type."""
    cli_config = normalize_cli_config(global_options, context)
    dg_context = DgContext.from_config_file_discovery_and_cli_config(Path.cwd(), cli_config)
    registry = RemoteComponentRegistry.from_dg_context(dg_context)
    if not registry.has(component_type):
        exit_with_error(f"No component type `{component_type}` could be resolved.")
    elif sum([description, scaffold_params_schema, component_params_schema]) > 1:
        exit_with_error(
            "Only one of --description, --scaffold-params-schema, and --component-params-schema can be specified."
        )

    component_type_metadata = registry.get(component_type)

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
        if component_type_metadata.scaffold_params_schema:
            click.echo("\nScaffold params schema:\n")
            click.echo(_serialize_json_schema(component_type_metadata.scaffold_params_schema))
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
@click.pass_context
def component_type_list(context: click.Context, **global_options: object) -> None:
    """List registered Dagster components in the current code location environment."""
    cli_config = normalize_cli_config(global_options, context)
    dg_context = DgContext.from_config_file_discovery_and_cli_config(Path.cwd(), cli_config)
    registry = RemoteComponentRegistry.from_dg_context(dg_context)
    for key in sorted(registry.keys()):
        click.echo(key)
        component_type = registry.get(key)
        if component_type.summary:
            click.echo(f"    {component_type.summary}")
