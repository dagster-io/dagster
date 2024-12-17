import json
import sys
from pathlib import Path
from typing import Any, Dict

import click

from dagster_components.core.component import ComponentMetadata, ComponentRegistry
from dagster_components.core.deployment import (
    CodeLocationProjectContext,
    is_inside_code_location_project,
)
from dagster_components.utils import CLI_BUILTIN_COMPONENT_LIB_KEY


@click.group(name="generate")
def list_cli():
    """Commands for listing Dagster components and related entities."""


@list_cli.command(name="component-types")
@click.pass_context
def list_component_types_command(ctx: click.Context) -> None:
    """List registered Dagster components."""
    builtin_component_lib = ctx.obj.get(CLI_BUILTIN_COMPONENT_LIB_KEY, False)
    if not is_inside_code_location_project(Path.cwd()):
        click.echo(
            click.style(
                "This command must be run inside a Dagster code location project.", fg="red"
            )
        )
        sys.exit(1)

    context = CodeLocationProjectContext.from_path(
        Path.cwd(),
        ComponentRegistry.from_entry_point_discovery(builtin_component_lib=builtin_component_lib),
    )
    output: Dict[str, Any] = {}
    for key, component_type in context.list_component_types():
        package, name = key.rsplit(".", 1)
        output[key] = ComponentMetadata(
            name=name,
            package=package,
            **component_type.get_metadata(),
        )
    click.echo(json.dumps(output))
