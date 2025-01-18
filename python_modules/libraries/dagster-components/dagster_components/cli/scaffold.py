import sys
from pathlib import Path
from typing import Optional

import click
from pydantic import TypeAdapter

from dagster_components import ComponentTypeRegistry
from dagster_components.core.deployment import (
    CodeLocationProjectContext,
    find_enclosing_code_location_root_path,
    is_inside_code_location_project,
)
from dagster_components.scaffold import (
    ComponentScaffolderUnavailableReason,
    scaffold_component_instance,
)
from dagster_components.utils import CLI_BUILTIN_COMPONENT_LIB_KEY


@click.group(name="scaffold")
def scaffold_cli() -> None:
    """Commands for scaffolding Dagster components and related entities."""


@scaffold_cli.command(name="component")
@click.argument("component_type", type=str)
@click.argument("component_name", type=str)
@click.option("--json-params", type=str, default=None)
@click.pass_context
def scaffold_component_command(
    ctx: click.Context,
    component_type: str,
    component_name: str,
    json_params: Optional[str],
) -> None:
    builtin_component_lib = ctx.obj.get(CLI_BUILTIN_COMPONENT_LIB_KEY, False)
    if not is_inside_code_location_project(Path.cwd()):
        click.echo(
            click.style(
                "This command must be run inside a Dagster code location project.", fg="red"
            )
        )
        sys.exit(1)

    context = CodeLocationProjectContext.from_code_location_path(
        find_enclosing_code_location_root_path(Path.cwd()),
        ComponentTypeRegistry.from_entry_point_discovery(
            builtin_component_lib=builtin_component_lib
        ),
    )
    if not context.has_component_type(component_type):
        click.echo(
            click.style(f"No component type `{component_type}` could be resolved.", fg="red")
        )
        sys.exit(1)

    component_type_cls = context.get_component_type(component_type)
    if json_params:
        scaffolder = component_type_cls.get_scaffolder()
        if isinstance(scaffolder, ComponentScaffolderUnavailableReason):
            raise Exception(
                f"Component type {component_type} does not have a scaffolder. Reason: {scaffolder.message}."
            )
        scaffold_params = TypeAdapter(scaffolder.get_params_schema_type()).validate_json(
            json_params
        )
    else:
        scaffold_params = {}

    scaffold_component_instance(
        context.components_path,
        component_name,
        component_type_cls,
        component_type,
        scaffold_params,
    )
