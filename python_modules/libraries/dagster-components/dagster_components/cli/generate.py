import sys
from pathlib import Path
from typing import Optional, Tuple

import click
from pydantic import TypeAdapter

from dagster_components import ComponentRegistry
from dagster_components.core.deployment import (
    CodeLocationProjectContext,
    is_inside_code_location_project,
)
from dagster_components.generate import generate_component_instance


@click.group(name="generate")
def generate_cli() -> None:
    """Commands for generating Dagster components and related entities."""


@generate_cli.command(name="component")
@click.argument("component_type", type=str)
@click.argument("component_name", type=str)
@click.option("--json-params", type=str, default=None)
@click.argument("extra_args", nargs=-1, type=str)
def generate_component_command(
    component_type: str,
    component_name: str,
    json_params: Optional[str],
    extra_args: Tuple[str, ...],
) -> None:
    if not is_inside_code_location_project(Path.cwd()):
        click.echo(
            click.style(
                "This command must be run inside a Dagster code location project.", fg="red"
            )
        )
        sys.exit(1)

    context = CodeLocationProjectContext.from_path(
        Path.cwd(), ComponentRegistry.from_entry_point_discovery()
    )
    if not context.has_component_type(component_type):
        click.echo(
            click.style(f"No component type `{component_type}` could be resolved.", fg="red")
        )
        sys.exit(1)

    component_type_cls = context.get_component_type(component_type)
    generate_params_schema = component_type_cls.generate_params_schema
    generate_params_cli = getattr(generate_params_schema, "cli", None)
    if generate_params_schema is None:
        generate_params = None
    elif json_params is not None:
        generate_params = TypeAdapter(generate_params_schema).validate_json(json_params)
    elif generate_params_cli is not None:
        inner_ctx = click.Context(generate_params_cli)
        generate_params_cli.parse_args(inner_ctx, list(extra_args))
        generate_params = inner_ctx.invoke(generate_params_schema.cli, **inner_ctx.params)
    else:
        generate_params = None

    generate_component_instance(
        context.component_instances_root_path,
        component_name,
        component_type_cls,
        component_type,
        generate_params,
    )
