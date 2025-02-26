import json
from typing import TYPE_CHECKING, Any, Literal, Union

import click
from pydantic import ConfigDict, TypeAdapter, create_model

from dagster_components.core.component import (
    Component,
    ComponentTypeMetadata,
    discover_component_types,
    discover_entry_point_component_types,
)
from dagster_components.utils import CLI_BUILTIN_COMPONENT_LIB_KEY

if TYPE_CHECKING:
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
    builtin_component_lib = ctx.obj.get(CLI_BUILTIN_COMPONENT_LIB_KEY, False)
    output: dict[str, Any] = {}
    registered_components: dict[ComponentKey, type[Component]] = {}
    if entry_points:
        registered_components.update(discover_entry_point_component_types(builtin_component_lib))
    if extra_modules:
        registered_components.update(discover_component_types(extra_modules))

    for key in sorted(registered_components.keys(), key=lambda k: k.to_typename()):
        output[key.to_typename()] = ComponentTypeMetadata(
            name=key.name,
            namespace=key.namespace,
            **registered_components[key].get_metadata(),
        )
    click.echo(json.dumps(output))


@list_cli.command(name="all-components-schema")
@click.pass_context
def list_all_components_schema_command(ctx: click.Context) -> None:
    """Builds a JSON schema which ORs the schema for a component
    file for all component types available in the current code location.
    """
    builtin_component_lib = ctx.obj.get(CLI_BUILTIN_COMPONENT_LIB_KEY, False)
    registered_components = discover_entry_point_component_types(builtin_component_lib)

    schemas = []
    for key in sorted(registered_components.keys(), key=lambda k: k.to_typename()):
        component_type = registered_components[key]
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
