import json
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

import click
from dagster_shared import check
from dagster_shared.record import as_dict
from dagster_shared.serdes import deserialize_value
from dagster_shared.serdes.objects import PackageObjectSnap
from dagster_shared.serdes.objects.definition_metadata import (
    DgAssetCheckMetadata,
    DgAssetMetadata,
    DgJobMetadata,
    DgScheduleMetadata,
    DgSensorMetadata,
)
from rich.console import Console
from rich.table import Table
from rich.text import Text

from dagster_dg.cli.shared_options import dg_global_options
from dagster_dg.component import PackageObjectFeature, RemotePackageRegistry
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.utils import DgClickCommand, DgClickGroup
from dagster_dg.utils.telemetry import cli_telemetry_wrapper


@click.group(name="list", cls=DgClickGroup)
def list_group():
    """Commands for listing Dagster entities."""


# ########################
# ##### HELPERS
# ########################


def DagsterInnerTable(columns: Sequence[str]) -> Table:
    table = Table(border_style="dim", show_lines=True)
    table.add_column(columns[0], style="bold cyan", no_wrap=True)
    for column in columns[1:]:
        table.add_column(column, style="bold")
    return table


def DagsterOuterTable(columns: Sequence[str]) -> Table:
    table = Table(border_style="dim")
    for column in columns:
        table.add_column(column, style="bold")
    return table


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
# ##### PACKAGE OBJECT
# ########################


FEATURE_COLOR_MAP = {"component": "deep_sky_blue3", "scaffold-target": "khaki1"}


def _pretty_features(obj: PackageObjectSnap) -> Text:
    text = Text()
    for entry_type in obj.features:
        if len(text) > 0:
            text += Text(", ")
        text += Text(entry_type, style=FEATURE_COLOR_MAP.get(entry_type, ""))
    text = Text("[") + text + Text("]")
    return text


def _package_object_table(entries: Sequence[PackageObjectSnap]) -> Table:
    sorted_entries = sorted(entries, key=lambda x: x.key.to_typename())
    table = DagsterInnerTable(["Symbol", "Summary", "Features"])
    for entry in sorted_entries:
        table.add_row(entry.key.to_typename(), entry.summary, _pretty_features(entry))
    return table


def _all_packages_object_table(
    registry: RemotePackageRegistry, name_only: bool, feature: Optional[PackageObjectFeature]
) -> Table:
    table = DagsterOuterTable(["Package"] if name_only else ["Package", "Objects"])

    for package in sorted(registry.packages):
        if not name_only:
            objs = registry.get_objects(package, feature)
            inner_table = _package_object_table(objs)
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
    "--feature",
    "-f",
    type=click.Choice(["component", "scaffold-target"]),
    help="Filter by entry type.",
)
@dg_global_options
@cli_telemetry_wrapper
def list_packages_command(
    name_only: bool,
    package: Optional[str],
    feature: Optional[PackageObjectFeature],
    **global_options: object,
) -> None:
    """List registered Dagster components in the current project environment."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_defined_registry_environment(Path.cwd(), cli_config)
    registry = RemotePackageRegistry.from_dg_context(dg_context)

    if package:
        table = _package_object_table(registry.get_objects(package, feature))
    else:
        table = _all_packages_object_table(registry, name_only, feature=feature)
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
            registry.get_objects(feature="component"), key=lambda x: x.key.to_typename()
        ):
            output.append({"key": entry.key.to_typename(), "summary": entry.summary})
        click.echo(json.dumps(output, indent=4))
    else:
        Console().print(_all_packages_object_table(registry, False, "component"))


# ########################
# ##### DEFS
# ########################


def _get_assets_table(assets: Sequence[DgAssetMetadata]) -> Table:
    table = DagsterInnerTable(["Key", "Group", "Deps", "Kinds", "Description"])
    table.columns[-1].max_width = 100

    for asset in sorted(assets, key=lambda x: x.key):
        description = Text(asset.description or "")
        description.truncate(max_width=100, overflow="ellipsis")
        table.add_row(
            asset.key,
            asset.group,
            "\n".join(asset.deps),
            "\n".join(asset.kinds),
            description,
        )
    return table


def _get_asset_checks_table(asset_checks: Sequence[DgAssetCheckMetadata]) -> Table:
    table = DagsterInnerTable(["Key", "Additional Deps", "Description"])
    table.columns[-1].max_width = 100

    for asset_check in sorted(asset_checks, key=lambda x: x.key):
        description = Text(asset_check.description or "")
        description.truncate(max_width=100, overflow="ellipsis")
        table.add_row(
            asset_check.key,
            "\n".join(asset_check.additional_deps),
            description,
        )
    return table


def _get_jobs_table(jobs: Sequence[DgJobMetadata]) -> Table:
    table = DagsterInnerTable(["Name"])

    for job in sorted(jobs, key=lambda x: x.name):
        table.add_row(job.name)
    return table


def _get_schedules_table(schedules: Sequence[DgScheduleMetadata]) -> Table:
    table = DagsterInnerTable(["Name", "Cron schedule"])

    for schedule in sorted(schedules, key=lambda x: x.name):
        table.add_row(schedule.name, schedule.cron_schedule)
    return table


def _get_sensors_table(sensors: Sequence[DgSensorMetadata]) -> Table:
    table = DagsterInnerTable(["Name"])

    for sensor in sorted(sensors, key=lambda x: x.name):
        table.add_row(sensor.name)
    return table


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
    definitions = check.is_list(deserialize_value(result))

    # JSON
    if output_json:  # pass it straight through
        json_output = [as_dict(defn) for defn in definitions]
        click.echo(json.dumps(json_output, indent=4))

    # TABLE
    else:
        assets = [item for item in definitions if isinstance(item, DgAssetMetadata)]
        asset_checks = [item for item in definitions if isinstance(item, DgAssetCheckMetadata)]
        jobs = [item for item in definitions if isinstance(item, DgJobMetadata)]
        schedules = [item for item in definitions if isinstance(item, DgScheduleMetadata)]
        sensors = [item for item in definitions if isinstance(item, DgSensorMetadata)]

        if len(definitions) == 0:
            click.echo("No definitions are defined for this project.")

        console = Console()

        table = Table(border_style="dim")
        table.add_column("Section", style="bold")
        table.add_column("Definitions")

        if assets:
            table.add_row("Assets", _get_assets_table(assets))
        if asset_checks:
            table.add_row("Asset Checks", _get_asset_checks_table(asset_checks))
        if jobs:
            table.add_row("Jobs", _get_jobs_table(jobs))
        if schedules:
            table.add_row("Schedules", _get_schedules_table(schedules))
        if sensors:
            table.add_row("Sensors", _get_sensors_table(sensors))

        console.print(table)
