import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import click

from dagster_components.core.component import (
    Component,
    ComponentTypeMetadata,
    ComponentTypeRegistry,
    get_component_type_name,
)
from dagster_components.core.component_decl_builder import find_local_component_types
from dagster_components.core.deployment import (
    CodeLocationProjectContext,
    find_enclosing_code_location_root_path,
    is_inside_code_location_project,
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
    if not is_inside_code_location_project(Path.cwd()):
        registry = ComponentTypeRegistry.from_entry_point_discovery(
            builtin_component_lib=builtin_component_lib
        )
        for key in sorted(registry.keys()):
            _add_component_type_to_output(output, key, registry.get(key))
    else:
        context = CodeLocationProjectContext.from_code_location_path(
            find_enclosing_code_location_root_path(Path.cwd()),
            ComponentTypeRegistry.from_entry_point_discovery(
                builtin_component_lib=builtin_component_lib
            ),
        )
        for key, component_type in context.list_component_types():
            _add_component_type_to_output(output, key, component_type)

    click.echo(json.dumps(output))


def _add_component_type_to_output(
    output: dict[str, Any], key: str, component_type: type[Component]
) -> None:
    package, name = key.rsplit(".", 1)
    output[key] = ComponentTypeMetadata(
        name=name,
        package=package,
        **component_type.get_metadata(),
    )


@list_cli.command(name="local-component-types")
@click.argument("component_directories", nargs=-1, type=click.Path(exists=True))
def list_local_component_types_command(component_directories: Sequence[str]) -> None:
    """List local Dagster components found in the specified directories."""
    output: list = []
    for component_directory in component_directories:
        for component_type in find_local_component_types(Path(component_directory)):
            output.append(
                {
                    "directory": component_directory,
                    "key": f".{get_component_type_name(component_type)}",
                    "metadata": ComponentTypeMetadata(
                        name=get_component_type_name(component_type),
                        package=component_directory,
                        **component_type.get_metadata(),
                    ),
                }
            )
    click.echo(json.dumps(output))
