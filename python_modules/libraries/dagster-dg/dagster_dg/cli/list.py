import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Any, Optional

import click
from dagster_shared.serdes.objects import PackageEntrySnap
from rich.console import Console
from rich.table import Table
from rich.text import Text

from dagster_dg.cli.shared_options import dg_global_options
from dagster_dg.component import PackageEntryType, RemotePackageRegistry
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.defs import (
    DgAssetMetadata,
    DgDefinitionMetadata,
    DgJobMetadata,
    DgScheduleMetadata,
    DgSensorMetadata,
)
from dagster_dg.error import DgError
from dagster_dg.utils import DgClickCommand, DgClickGroup
from dagster_dg.utils.telemetry import cli_telemetry_wrapper


@click.group(name="list", cls=DgClickGroup)
def list_group():
    """Commands for listing Dagster entities."""


# ########################
# ##### PROJECT
# ########################


@list_group.command(name="project", cls=DgClickCommand)
@dg_global_options
@cli_telemetry_wrapper
def list_project_command(**global_options: object) -> None:
    """List projects in the current workspace."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_workspace_environment(Path.cwd(), cli_config)

    for project in dg_context.project_specs:
        click.echo(project.path)


# ########################
# ##### COMPONENT
# ########################


@list_group.command(name="component", cls=DgClickCommand)
@dg_global_options
@cli_telemetry_wrapper
def list_component_command(**global_options: object) -> None:
    """List Dagster component instances defined in the current project."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_project_environment(Path.cwd(), cli_config)

    for component_instance_name in dg_context.get_component_instance_names():
        click.echo(component_instance_name)


# ########################
# ##### PACKAGE ENTRY
# ########################


ENTRY_TYPE_COLOR_MAP = {"component": "deep_sky_blue3", "scaffold-target": "khaki1"}


def _pretty_entry_types(entry: PackageEntrySnap) -> Text:
    text = Text()
    for entry_type in entry.types:
        if len(text) > 0:
            text += Text(", ")
        text += Text(entry_type, style=ENTRY_TYPE_COLOR_MAP.get(entry_type, ""))
    text = Text("[") + text + Text("]")
    return text


def _package_entry_table(entries: Sequence[PackageEntrySnap]) -> Table:
    sorted_entries = sorted(entries, key=lambda x: x.key.to_typename())
    table = Table(border_style="dim", show_lines=True)
    table.add_column("Key", style="bold cyan", no_wrap=True)
    table.add_column("Summary")
    table.add_column("Types")
    for entry in sorted_entries:
        table.add_row(entry.key.to_typename(), entry.summary, _pretty_entry_types(entry))
    return table


def _all_packages_entry_table(
    registry: RemotePackageRegistry, name_only: bool, entry_type: Optional[PackageEntryType]
) -> Table:
    table = Table(border_style="dim")

    table.add_column("Package", style="bold")
    if not name_only:
        table.add_column("Entries", style="bold")

    for package in sorted(registry.packages):
        if not name_only:
            entries = registry.get_entries(package, entry_type)
            inner_table = _package_entry_table(entries)
            table.add_row(package, inner_table)
        else:
            table.add_row(package)
    return table


@list_group.command(name="packages", cls=DgClickCommand)
@click.option(
    "--name-only",
    is_flag=True,
    default=False,
    help="Only display the names of the packages.",
)
@click.option(
    "--package",
    "-p",
    help="Filter by package name.",
)
@click.option(
    "--entry-type",
    "-t",
    type=click.Choice(["component", "scaffold-target"]),
    help="Filter by entry type.",
)
@dg_global_options
@cli_telemetry_wrapper
def list_packages_command(
    name_only: bool,
    package: Optional[str],
    entry_type: Optional[PackageEntryType],
    **global_options: object,
) -> None:
    """List registered Dagster components in the current project environment."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_defined_registry_environment(Path.cwd(), cli_config)
    registry = RemotePackageRegistry.from_dg_context(dg_context)

    if package:
        table = _package_entry_table(registry.get_entries(package, entry_type))
    else:
        table = _all_packages_entry_table(registry, name_only, entry_type=entry_type)
    Console().print(table)


@list_group.command(name="component-type", cls=DgClickCommand)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="Output as JSON instead of a table.",
)
@dg_global_options
@cli_telemetry_wrapper
def list_component_type_command(output_json: bool, **global_options: object) -> None:
    """List registered Dagster components in the current project environment."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_defined_registry_environment(Path.cwd(), cli_config)
    registry = RemotePackageRegistry.from_dg_context(dg_context)

    if output_json:
        output: list[dict[str, object]] = []
        for entry in sorted(
            registry.get_entries(entry_type="component"), key=lambda x: x.key.to_typename()
        ):
            output.append({"key": entry.key.to_typename(), "summary": entry.summary})
        click.echo(json.dumps(output, indent=4))
    else:
        Console().print(_all_packages_entry_table(registry, False, "component"))


# ########################
# ##### DEFS
# ########################


@list_group.command(name="defs", cls=DgClickCommand)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="Output as JSON instead of a table.",
)
@dg_global_options
@cli_telemetry_wrapper
def list_defs_command(output_json: bool, **global_options: object) -> None:
    """List registered Dagster definitions in the current project environment."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_project_environment(Path.cwd(), cli_config)

    result = dg_context.external_components_command(
        [
            "list",
            "definitions",
            "-m",
            dg_context.code_location_target_module_name,
        ],
        # Sets the "--location" option for "dagster-components definitions list"
        # using the click auto-envvar prefix for backwards compatibility on older versions
        # before that option was added
        additional_env={"DG_CLI_LIST_DEFINITIONS_LOCATION": dg_context.code_location_name},
    )
    definitions = [_resolve_definition(x) for x in json.loads(result)]

    # JSON
    if output_json:  # pass it straight through
        json_output = [asdict(defn) for defn in definitions]
        click.echo(json.dumps(json_output, indent=4))

    # TABLE
    else:
        assets = [item for item in definitions if isinstance(item, DgAssetMetadata)]
        jobs = [item for item in definitions if isinstance(item, DgJobMetadata)]
        schedules = [item for item in definitions if isinstance(item, DgScheduleMetadata)]
        sensors = [item for item in definitions if isinstance(item, DgSensorMetadata)]

        if len(definitions) == 0:
            click.echo("No definitions are defined for this project.")

        console = Console()
        if assets:
            click.echo("Assets")
            table = Table(border_style="dim")
            table.add_column("Key")
            table.add_column("Group")
            table.add_column("Deps")
            table.add_column("Kinds")
            table.add_column("Description")

            for asset in sorted(assets, key=lambda x: x.key):
                table.add_row(
                    asset.key,
                    asset.group,
                    "\n".join(asset.deps),
                    "\n".join(asset.kinds),
                    asset.description,
                )
            console.print(table)
            click.echo("")

        if jobs:
            click.echo("Jobs")
            table = Table(border_style="dim")
            table.add_column("Name")

            for schedule in schedules:
                table.add_row(schedule.name)
            console.print(table)
            click.echo("")

        if schedules:
            click.echo("Schedules")
            table = Table(border_style="dim")
            table.add_column("Name")
            table.add_column("Cron schedule")

            for schedule in schedules:
                table.add_row(schedule.name, schedule.cron_schedule)
            console.print(table)
            click.echo("")

        if sensors:
            click.echo("Sensors")
            table = Table(border_style="dim")
            table.add_column("Name")

            for schedule in schedules:
                table.add_row(schedule.name)
            console.print(table)


def _resolve_definition(item: dict[str, Any]) -> DgDefinitionMetadata:
    if item["type"] == "asset":
        return DgAssetMetadata(**item)
    elif item["type"] == "job":
        return DgJobMetadata(**item)
    elif item["type"] == "schedule":
        return DgScheduleMetadata(**item)
    elif item["type"] == "sensor":
        return DgSensorMetadata(**item)
    else:
        raise DgError(f"Unexpected item type: {item['type']}")
