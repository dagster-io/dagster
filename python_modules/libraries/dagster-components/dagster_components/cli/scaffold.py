from pathlib import Path
from typing import Optional

import click
from pydantic import TypeAdapter

from dagster_components import ComponentTypeRegistry
from dagster_components.core.component_key import GlobalComponentKey
from dagster_components.scaffold import (
    ComponentScaffolderUnavailableReason,
    scaffold_component_instance,
)
from dagster_components.utils import CLI_BUILTIN_COMPONENT_LIB_KEY, exit_with_error


@click.group(name="scaffold")
def scaffold_cli() -> None:
    """Commands for scaffolding Dagster components and related entities."""


@scaffold_cli.command(name="component")
@click.argument("component_type", type=str)
@click.argument("component_path", type=Path)
@click.option("--json-params", type=str, default=None)
@click.pass_context
def scaffold_component_command(
    ctx: click.Context,
    component_type: str,
    component_path: Path,
    json_params: Optional[str],
) -> None:
    builtin_component_lib = ctx.obj.get(CLI_BUILTIN_COMPONENT_LIB_KEY, False)
    registry = ComponentTypeRegistry.from_entry_point_discovery(
        builtin_component_lib=builtin_component_lib
    )
    component_key = GlobalComponentKey.from_typename(component_type)
    if not registry.has(component_key):
        exit_with_error(f"No component type `{component_type}` could be resolved.")

    component_type_cls = registry.get(component_key)
    if json_params:
        scaffolder = component_type_cls.get_scaffolder()
        if isinstance(scaffolder, ComponentScaffolderUnavailableReason):
            raise Exception(
                f"Component type {component_type} does not have a scaffolder. Reason: {scaffolder.message}."
            )
        scaffold_params = TypeAdapter(scaffolder.get_schema()).validate_json(json_params)
    else:
        scaffold_params = {}

    scaffold_component_instance(
        component_path,
        component_type_cls,
        component_type,
        scaffold_params,
    )
