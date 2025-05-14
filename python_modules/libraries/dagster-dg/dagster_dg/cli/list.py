import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Optional

import click
from dagster_shared.ipc import ipc_tempfile
from dagster_shared.record import as_dict
from dagster_shared.serdes import deserialize_value
from dagster_shared.serdes.errors import DeserializationError
from dagster_shared.serdes.objects import PluginObjectSnap
from dagster_shared.serdes.objects.definition_metadata import (
    DgAssetCheckMetadata,
    DgAssetMetadata,
    DgDefinitionMetadata,
    DgJobMetadata,
    DgScheduleMetadata,
    DgSensorMetadata,
)
from packaging.version import Version
from rich.console import Console
from rich.table import Table
from rich.text import Text

from dagster_dg.cli.shared_options import dg_global_options, dg_path_options
from dagster_dg.component import PluginObjectFeature, RemotePluginRegistry
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.env import ProjectEnvVars, get_project_specified_env_vars
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


@list_group.command(name="projects", aliases=["project"], cls=DgClickCommand)
@dg_global_options
@dg_path_options
@cli_telemetry_wrapper
def list_project_command(path: Path, **global_options: object) -> None:
    """List projects in the current workspace."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_workspace_environment(path, cli_config)

    for project in dg_context.project_specs:
        click.echo(project.path)


# ########################
# ##### COMPONENT
# ########################


@list_group.command(name="components", aliases=["component"], cls=DgClickCommand)
@dg_path_options
@dg_global_options
@cli_telemetry_wrapper
def list_component_command(path: Path, **global_options: object) -> None:
    """List Dagster component instances defined in the current project."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_project_environment(path, cli_config)

    for component_instance_name in dg_context.get_component_instance_names():
        click.echo(component_instance_name)


# ########################
# ##### PLUGINS
# ########################


FEATURE_COLOR_MAP = {"component": "deep_sky_blue3", "scaffold-target": "khaki1"}


def _pretty_features(obj: PluginObjectSnap) -> Text:
    text = Text()
    for entry_type in obj.features:
        if len(text) > 0:
            text += Text(", ")
        text += Text(entry_type, style=FEATURE_COLOR_MAP.get(entry_type, ""))
    text = Text("[") + text + Text("]")
    return text


def _plugin_object_table(entries: Sequence[PluginObjectSnap]) -> Table:
    sorted_entries = sorted(entries, key=lambda x: x.key.to_typename())
    table = DagsterInnerTable(["Symbol", "Summary", "Features"])
    for entry in sorted_entries:
        table.add_row(entry.key.to_typename(), entry.summary, _pretty_features(entry))
    return table


def _all_plugins_object_table(
    registry: RemotePluginRegistry, name_only: bool, feature: Optional[PluginObjectFeature]
) -> Table:
    table = DagsterOuterTable(["Plugin"] if name_only else ["Plugin", "Objects"])

    for package in sorted(registry.packages):
        if not name_only:
            objs = registry.get_objects(package, feature)
            if objs:  # only add the row if there are objects
                inner_table = _plugin_object_table(objs)
                table.add_row(package, inner_table)
        else:
            table.add_row(package)
    return table


@list_group.command(name="plugins", aliases=["plugin"], cls=DgClickCommand)
@click.option(
    "--name-only",
    is_flag=True,
    default=False,
    help="Only display the names of the plugin packages.",
)
@click.option(
    "--plugin",
    "-p",
    help="Filter by plugin name.",
)
@click.option(
    "--feature",
    "-f",
    type=click.Choice(["component", "scaffold-target"]),
    help="Filter by object type.",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="Output as JSON instead of a table.",
)
@dg_path_options
@dg_global_options
@cli_telemetry_wrapper
def list_plugins_command(
    name_only: bool,
    plugin: Optional[str],
    feature: Optional[PluginObjectFeature],
    output_json: bool,
    path: Path,
    **global_options: object,
) -> None:
    """List dg plugins and their corresponding objects in the current Python environment."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_defined_registry_environment(path, cli_config)
    registry = RemotePluginRegistry.from_dg_context(dg_context)
    # pp(registry.get_objects())

    if output_json:
        output: list[dict[str, object]] = []
        for entry in sorted(registry.get_objects(), key=lambda x: x.key.to_typename()):
            output.append(
                {
                    "key": entry.key.to_typename(),
                    "summary": entry.summary,
                    "features": entry.features,
                }
            )
        click.echo(json.dumps(output, indent=4))
    else:  # table output
        if plugin:
            table = _plugin_object_table(registry.get_objects(plugin, feature))
        else:
            table = _all_plugins_object_table(registry, name_only, feature=feature)
        Console().print(table)


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


# On older versions of `dagster`, `dagster-components list defs` output was written directly to
# stdout, where it was possibly polluted by other output from user code. This scans raw stdout for
# the line containing the output.
def _extract_list_defs_output_from_raw_output(raw_output: str) -> list[Any]:
    last_decode_error = None
    for line in raw_output.splitlines():
        try:
            defs_list = deserialize_value(line, as_type=list[DgDefinitionMetadata])
            return defs_list
        except (json.JSONDecodeError, DeserializationError) as e:
            last_decode_error = e

    if last_decode_error:
        raise last_decode_error

    raise Exception(
        "Did not successfully parse definitions list. Full stdout of subprocess:\n" + raw_output
    )


MIN_DAGSTER_COMPONENTS_LIST_DEFINITIONS_LOCATION_OPTION_VERSION = Version("1.10.8")
MIN_DAGSTER_COMPONENTS_LIST_DEFINITIONS_OUTPUT_FILE_OPTION_VERSION = Version("1.10.12")


@list_group.command(name="defs", aliases=["def"], cls=DgClickCommand)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="Output as JSON instead of a table.",
)
@dg_path_options
@dg_global_options
@cli_telemetry_wrapper
def list_defs_command(output_json: bool, path: Path, **global_options: object) -> None:
    """List registered Dagster definitions in the current project environment."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_project_environment(path, cli_config)

    # On newer versions, we use a dedicated channel in the form of a tempfile that will _only_ have
    # the expected output written to it.
    if (
        dg_context.dagster_version
        >= MIN_DAGSTER_COMPONENTS_LIST_DEFINITIONS_OUTPUT_FILE_OPTION_VERSION
    ):
        with ipc_tempfile() as temp_file:
            dg_context.external_components_command(
                [
                    "list",
                    "definitions",
                    "--location",
                    dg_context.code_location_name,
                    "--module-name",
                    dg_context.code_location_target_module_name,
                    "--output-file",
                    temp_file,
                ],
            )
            definitions = deserialize_value(
                Path(temp_file).read_text(), as_type=list[DgDefinitionMetadata]
            )

    # On older versions, we extract the output from the raw stdout of the command.
    else:
        location_opts = (
            ["--location", dg_context.code_location_name]
            if dg_context.dagster_version
            >= MIN_DAGSTER_COMPONENTS_LIST_DEFINITIONS_LOCATION_OPTION_VERSION
            else []
        )
        output = dg_context.external_components_command(
            [
                "list",
                "definitions",
                "--module-name",
                dg_context.code_location_target_module_name,
                *location_opts,
            ],
        )
        definitions = _extract_list_defs_output_from_raw_output(output)

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
            return

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


# ########################
# ##### ENVIRONMENT
# ########################


@list_group.command(name="envs", aliases=["env"], cls=DgClickCommand)
@dg_path_options
@dg_global_options
@cli_telemetry_wrapper
def list_env_command(path: Path, **global_options: object) -> None:
    """List environment variables from the .env file of the current project."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_project_environment(path, cli_config)

    env = ProjectEnvVars.from_ctx(dg_context)
    used_env_vars = get_project_specified_env_vars(dg_context)

    if not env.values and not used_env_vars:
        click.echo("No environment variables are defined for this project.")
        return

    table = Table(border_style="dim")
    table.add_column("Env Var")
    table.add_column("Value")
    table.add_column("Components")
    env_var_keys = env.values.keys() | used_env_vars.keys()
    for key in sorted(env_var_keys):
        components = used_env_vars.get(key, [])
        table.add_row(key, env.values.get(key), ", ".join(str(path) for path in components))

    console = Console()
    console.print(table)
