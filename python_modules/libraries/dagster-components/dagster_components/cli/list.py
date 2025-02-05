import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Literal, Union

import click
from pydantic import TypeAdapter, create_model

from dagster_components.core.component import (
    ComponentTypeMetadata,
    ComponentTypeRegistry,
    find_local_component_types,
)
from dagster_components.utils import CLI_BUILTIN_COMPONENT_LIB_KEY


@click.group(name="list")
def list_cli():
    """Commands for listing Dagster components and related entities."""


@list_cli.command(name="component-types")
@click.pass_context
def list_component_types_command(ctx: click.Context) -> None:
    """List registered Dagster components."""
    builtin_component_lib = ctx.obj.get(CLI_BUILTIN_COMPONENT_LIB_KEY, False)
    output: dict[str, Any] = {}
    registry = ComponentTypeRegistry.from_entry_point_discovery(
        builtin_component_lib=builtin_component_lib
    )
    for key in sorted(registry.keys(), key=lambda k: k.to_typename()):
        output[key.to_typename()] = ComponentTypeMetadata(
            name=key.name,
            namespace=key.namespace,
            **registry.get(key).get_metadata(),
        )
    click.echo(json.dumps(output))


@list_cli.command(name="local-component-types")
@click.argument("component_directories", nargs=-1, type=click.Path(exists=True))
def list_local_component_types_command(component_directories: Sequence[str]) -> None:
    """List local Dagster components found in the specified directories."""
    output: dict = {}
    for component_directory in component_directories:
        output_for_directory = {}
        for key, component_type in find_local_component_types(Path(component_directory)).items():
            output_for_directory[key.to_typename()] = ComponentTypeMetadata(
                name=key.name,
                namespace=key.namespace,
                **component_type.get_metadata(),
            )
        if len(output_for_directory) > 0:
            output[component_directory] = output_for_directory
    click.echo(json.dumps(output))


@list_cli.command(name="all-components-schema")
@click.pass_context
def list_all_components_schema_command(ctx: click.Context) -> None:
    """Builds a JSON schema which ORs the schema for a component
    file for all component types available in the current code location.
    """
    builtin_component_lib = ctx.obj.get(CLI_BUILTIN_COMPONENT_LIB_KEY, False)
    registry = ComponentTypeRegistry.from_entry_point_discovery(
        builtin_component_lib=builtin_component_lib
    )

    schemas = []
    for key in sorted(registry.keys(), key=lambda k: k.to_typename()):
        component_type = registry.get(key)
        # Create ComponentFileModel schema for each type
        schema_type = component_type.get_schema()
        key_string = key.to_typename()
        if schema_type:
            schemas.append(
                create_model(
                    key.name, type=(Literal[key_string], key_string), params=(schema_type, None)
                )
            )
    union_type = Union[tuple(schemas)]  # type: ignore
    click.echo(json.dumps(TypeAdapter(union_type).json_schema()))
