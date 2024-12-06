import json
import sys
from pathlib import Path
from typing import Any, Dict

import click

from dagster_components.core.component import ComponentRegistry
from dagster_components.core.deployment import (
    CodeLocationProjectContext,
    is_inside_code_location_project,
)


@click.group(name="generate")
def list_cli():
    """Commands for listing Dagster components and related entities."""


@list_cli.command(name="component-types")
def list_component_types_command() -> None:
    """List registered Dagster components."""
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
    output: Dict[str, Any] = {}
    for component_type in context.list_component_types():
        # package, name = component_type.rsplit(".", 1)
        output[component_type] = {
            "name": component_type,
        }
    click.echo(json.dumps(output))
