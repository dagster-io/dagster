import json
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from dagster_dg.cli.global_options import dg_global_options
from dagster_dg.component import RemoteComponentRegistry
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.utils import DgClickCommand, DgClickGroup


@click.group(name="list", cls=DgClickGroup)
def list_group():
    """Commands for listing Dagster entities."""


# ########################
# ##### CODE LOCATION
# ########################


@list_group.command(name="code-location", cls=DgClickCommand)
@dg_global_options
@click.pass_context
def code_location_list_command(context: click.Context, **global_options: object) -> None:
    """List code locations in the current deployment."""
    cli_config = normalize_cli_config(global_options, context)
    dg_context = DgContext.for_deployment_environment(Path.cwd(), cli_config)

    for code_location in dg_context.get_code_location_names():
        click.echo(code_location)


# ########################
# ##### COMPONENT
# ########################


@list_group.command(name="component", cls=DgClickCommand)
@dg_global_options
@click.pass_context
def component_list_command(context: click.Context, **global_options: object) -> None:
    """List Dagster component instances defined in the current code location."""
    cli_config = normalize_cli_config(global_options, context)
    dg_context = DgContext.for_code_location_environment(Path.cwd(), cli_config)

    for component_instance_name in dg_context.get_component_instance_names():
        click.echo(component_instance_name)


# ########################
# ##### COMPONENT TYPE
# ########################


@list_group.command(name="component-type", cls=DgClickCommand)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="Output as JSON instead of a table.",
)
@dg_global_options
@click.pass_context
def component_type_list(
    context: click.Context, output_json: bool, **global_options: object
) -> None:
    """List registered Dagster components in the current code location environment."""
    cli_config = normalize_cli_config(global_options, context)
    dg_context = DgContext.for_defined_registry_environment(Path.cwd(), cli_config)
    registry = RemoteComponentRegistry.from_dg_context(dg_context)

    sorted_keys = sorted(registry.global_keys(), key=lambda k: k.to_typename())

    # JSON
    if output_json:
        output: list[dict[str, object]] = []
        for key in sorted_keys:
            component_type_metadata = registry.get_global(key)
            output.append(
                {
                    "key": key.to_typename(),
                    "summary": component_type_metadata.summary,
                }
            )
        click.echo(json.dumps(output, indent=4))

    # TABLE
    else:
        table = Table(border_style="dim")
        table.add_column("Component Type", style="bold cyan", no_wrap=True)
        table.add_column("Summary")
        for key in sorted(registry.global_keys(), key=lambda k: k.to_typename()):
            table.add_row(key.to_typename(), registry.get_global(key).summary)
        console = Console()
        console.print(table)
