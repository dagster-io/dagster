import json
from typing import Any, Literal, Union

import click
from pydantic import ConfigDict, TypeAdapter, create_model

from dagster_components.core.component import (
    Component,
    ComponentTypeMetadata,
    discover_component_types,
    discover_entry_point_component_types,
)
from dagster_components.core.component_key import ComponentKey


@click.group(name="list")
def list_cli():
    """Commands for listing Dagster components and related entities."""


@list_cli.command(name="component-types")
@click.option("--entry-points/--no-entry-points", is_flag=True, default=True)
@click.argument("extra_modules", nargs=-1, type=str)
@click.pass_context
def list_component_types_command(
    ctx: click.Context, entry_points: bool, extra_modules: tuple[str, ...]
) -> None:
    """List registered Dagster components."""
    output: dict[str, Any] = {}
    component_types = _load_component_types(entry_points, extra_modules)
    for key in sorted(component_types.keys(), key=lambda k: k.to_typename()):
        output[key.to_typename()] = ComponentTypeMetadata(
            name=key.name,
            namespace=key.namespace,
            **component_types[key].get_metadata(),
        )
    click.echo(json.dumps(output))


@list_cli.command(name="all-components-schema")
@click.option("--entry-points/--no-entry-points", is_flag=True, default=True)
@click.argument("extra_modules", nargs=-1, type=str)
def list_all_components_schema_command(entry_points: bool, extra_modules: tuple[str, ...]) -> None:
    """Builds a JSON schema which ORs the schema for a component
    file for all component types available in the current code location.
    """
    component_types = _load_component_types(entry_points, extra_modules)

    schemas = []
    for key in sorted(component_types.keys(), key=lambda k: k.to_typename()):
        component_type = component_types[key]
        # Create ComponentFileModel schema for each type
        schema_type = component_type.get_schema()
        key_string = key.to_typename()
        if schema_type:
            schemas.append(
                create_model(
                    key.name,
                    type=(Literal[key_string], key_string),
                    attributes=(schema_type, None),
                    __config__=ConfigDict(extra="forbid"),
                )
            )
    union_type = Union[tuple(schemas)]  # type: ignore
    click.echo(json.dumps(TypeAdapter(union_type).json_schema()))


# ########################
# ##### HELPERS
# ########################


def _load_component_types(
    entry_points: bool, extra_modules: tuple[str, ...]
) -> dict[ComponentKey, type[Component]]:
    component_types = {}
    if entry_points:
        component_types.update(discover_entry_point_component_types())
    if extra_modules:
        component_types.update(discover_component_types(extra_modules))
    return component_types
