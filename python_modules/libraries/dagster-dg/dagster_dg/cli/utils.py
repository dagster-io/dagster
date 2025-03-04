import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import click

from dagster_dg.cli.shared_options import dg_global_options
from dagster_dg.component import RemoteComponentRegistry, all_components_schema_from_dg_context
from dagster_dg.component_key import ComponentKey
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.utils import (
    DgClickCommand,
    DgClickGroup,
    exit_with_error,
    generate_missing_component_type_error_message,
)
from dagster_dg.utils.editor import (
    install_or_update_yaml_schema_extension,
    recommend_yaml_extension,
)

_DEFAULT_SCHEMA_FOLDER_NAME = ".vscode"


@click.group(name="utils", cls=DgClickGroup)
def utils_group():
    """Assorted utility commands."""


@utils_group.command(name="configure-editor", cls=DgClickCommand)
@dg_global_options
@click.argument("editor", type=click.Choice(["vscode", "cursor"]))
def configure_editor_command(
    editor: str,
    **global_options: object,
) -> None:
    """Generates and installs a VS Code or Cursor extension which provides JSON schemas for Components types specified by YamlComponentsLoader objects."""
    executable_name = "code" if editor == "vscode" else "cursor"

    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_project_environment(Path.cwd(), cli_config)

    recommend_yaml_extension(executable_name)

    schema_folder = dg_context.root_path / _DEFAULT_SCHEMA_FOLDER_NAME
    schema_folder.mkdir(exist_ok=True)

    schema_path = schema_folder / "schema.json"
    schema_path.write_text(json.dumps(all_components_schema_from_dg_context(dg_context), indent=2))

    install_or_update_yaml_schema_extension(executable_name, dg_context.root_path, schema_path)


# ########################
# ##### INSPECT COMPONENT TYPE
# ########################


@utils_group.command(name="inspect-component-type", cls=DgClickCommand)
@click.argument("component_type", type=str)
@click.option("--description", is_flag=True, default=False)
@click.option("--scaffold-params-schema", is_flag=True, default=False)
@click.option("--component-schema", is_flag=True, default=False)
@dg_global_options
def inspect_component_type_command(
    component_type: str,
    description: bool,
    scaffold_params_schema: bool,
    component_schema: bool,
    **global_options: object,
) -> None:
    """Get detailed information on a registered Dagster component type."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_defined_registry_environment(Path.cwd(), cli_config)
    registry = RemoteComponentRegistry.from_dg_context(dg_context)
    component_key = ComponentKey.from_typename(component_type)
    if not registry.has(component_key):
        exit_with_error(generate_missing_component_type_error_message(component_type))
    elif sum([description, scaffold_params_schema, component_schema]) > 1:
        exit_with_error(
            "Only one of --description, --scaffold-params-schema, and --component-schema can be specified."
        )

    component_type_metadata = registry.get(component_key)

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
