import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import click
from dagster_dg_core.component import EnvRegistry
from dagster_dg_core.config import normalize_cli_config
from dagster_dg_core.context import DgContext
from dagster_dg_core.env import ProjectEnvVars, get_project_specified_env_vars
from dagster_dg_core.shared_options import dg_global_options, dg_path_options
from dagster_dg_core.utils import DgClickCommand, DgClickGroup, capture_stdout
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.serdes.objects.definition_metadata import (
    DgAssetCheckMetadata,
    DgAssetMetadata,
    DgJobMetadata,
    DgResourceMetadata,
    DgScheduleMetadata,
    DgSensorMetadata,
)
from dagster_shared.utils.warnings import disable_dagster_warnings
from rich.console import Console
from rich.text import Text

from dagster_dg_cli.utils.plus import gql
from dagster_dg_cli.utils.plus.gql_client import DagsterPlusGraphQLClient

if TYPE_CHECKING:
    from rich.table import Table


@click.group(name="list", cls=DgClickGroup)
def list_group():
    """Commands for listing Dagster entities."""


# ########################
# ##### HELPERS
# ########################


def DagsterInnerTable(columns: Sequence[str]) -> "Table":
    from rich.table import Table

    table = Table(border_style="dim", show_lines=True)
    table.add_column(columns[0], style="bold cyan", no_wrap=True)
    for column in columns[1:]:
        table.add_column(column, style="bold")
    return table


def DagsterOuterTable(columns: Sequence[str]) -> "Table":
    from rich.table import Table

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
def list_project_command(target_path: Path, **global_options: object) -> None:
    """List projects in the current workspace or emit the current project directory."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_workspace_or_project_environment(target_path, cli_config)

    if dg_context.is_in_workspace:
        # In a workspace, list all projects with their relative paths
        for project in dg_context.project_specs:
            click.echo(project.path)
    elif dg_context.is_project:
        # In a standalone project (not in a workspace), emit the current directory
        # This allows the command to work in both contexts for CI/CD workflows
        click.echo(".")


# ########################
# ##### COMPONENT
# ########################


@list_group.command(name="components", aliases=["component"], cls=DgClickCommand)
@click.option(
    "--package",
    "-p",
    help="Filter by package name.",
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
def list_components_command(
    target_path: Path, package: Optional[str], output_json: bool, **global_options: object
) -> None:
    """List all available Dagster component types in the current Python environment."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.from_file_discovery_and_command_line_config(target_path, cli_config)
    registry = EnvRegistry.from_dg_context(dg_context)

    # Get all components (objects that have the 'component' feature)
    component_objects = sorted(
        registry.get_objects(feature="component"), key=lambda x: x.key.to_typename()
    )
    if package:
        # Filter by package name. Can accept a dot-separated module name for finer granularity.
        component_objects = [
            obj
            for obj in component_objects
            if obj.key.namespace == package or obj.key.namespace.startswith(f"{package}.")
        ]

    if output_json:
        output = [
            {"key": obj.key.to_typename(), "summary": obj.summary} for obj in component_objects
        ]
        click.echo(json.dumps(output))
    else:
        # Create a table with component types
        table = DagsterInnerTable(["Key", "Summary"])
        for component in sorted(component_objects, key=lambda x: x.key.to_typename()):
            table.add_row(component.key.to_typename(), component.summary)
        Console().print(table)


# ########################
# ##### PLUGINS
# ########################


FEATURE_COLOR_MAP = {"component": "deep_sky_blue3", "scaffold-target": "khaki1"}


@list_group.command(name="registry-modules", aliases=["registry-module"], cls=DgClickCommand)
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
def list_registry_modules_command(
    output_json: bool,
    target_path: Path,
    **global_options: object,
) -> None:
    """List dg plugins and their corresponding objects in the current Python environment."""
    from rich.console import Console

    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.from_file_discovery_and_command_line_config(target_path, cli_config)
    registry = EnvRegistry.from_dg_context(dg_context)

    if output_json:
        json_output = [{"module": module} for module in sorted(registry.modules)]
        click.echo(json.dumps(json_output))
    else:
        table = DagsterOuterTable(["Module"])
        for module in sorted(registry.modules):
            table.add_row(module)
        Console().print(table)


# ########################
# ##### DEFS
# ########################


def _defs_column_from_str(column: str) -> "DefsColumn":
    if column == "name":
        return DefsColumn.KEY
    try:
        return DefsColumn(column.lower())
    except ValueError as e:
        try:
            # Attempt to pluralize singular inputs
            return DefsColumn(column.lower() + "s")
        except ValueError:
            raise e


class DefsColumn(str, Enum):
    KEY = "key"
    GROUP = "group"
    DEPS = "deps"
    KINDS = "kinds"
    DESCRIPTION = "description"
    TAGS = "tags"
    CRON = "cron"
    IS_EXECUTABLE = "is_executable"


# columns that are potentially truncated
_TRUNCATED_COLUMN_WIDTHS = {
    DefsColumn.DESCRIPTION: 100,
}


class DefsType(str, Enum):
    ASSET = "asset"
    ASSET_CHECK = "asset_check"
    JOB = "job"
    RESOURCE = "resource"
    SCHEDULE = "schedule"
    SENSOR = "sensor"


DEFAULT_COLUMNS = [
    DefsColumn.KEY,
    DefsColumn.GROUP,
    DefsColumn.DEPS,
    DefsColumn.KINDS,
    DefsColumn.DESCRIPTION,
    DefsColumn.CRON,
]


def _supports_column(column: DefsColumn, defs_type: DefsType) -> bool:
    if column == DefsColumn.KEY:
        return True
    elif column == DefsColumn.GROUP:
        return defs_type in (DefsType.ASSET,)
    elif column == DefsColumn.DEPS:
        return defs_type in (DefsType.ASSET, DefsType.ASSET_CHECK)
    elif column == DefsColumn.KINDS:
        return defs_type in (DefsType.ASSET,)
    elif column == DefsColumn.DESCRIPTION:
        return defs_type in (DefsType.ASSET, DefsType.ASSET_CHECK, DefsType.JOB)
    elif column == DefsColumn.TAGS:
        return defs_type in (DefsType.ASSET,)
    elif column == DefsColumn.CRON:
        return defs_type in (DefsType.SCHEDULE,)
    elif column == DefsColumn.IS_EXECUTABLE:
        return defs_type in (DefsType.ASSET,)
    else:
        raise ValueError(f"Invalid column: {column}")


def _get_asset_value(column: DefsColumn, asset: DgAssetMetadata) -> Optional[str]:
    if column == DefsColumn.KEY:
        return asset.key
    elif column == DefsColumn.GROUP:
        return asset.group
    elif column == DefsColumn.DEPS:
        return "\n".join(asset.deps)
    elif column == DefsColumn.KINDS:
        return "\n".join(asset.kinds)
    elif column == DefsColumn.DESCRIPTION:
        return asset.description
    elif column == DefsColumn.TAGS:
        return "\n".join(asset.tags)
    elif column == DefsColumn.IS_EXECUTABLE:
        return str(asset.is_executable)
    else:
        raise ValueError(f"Invalid column: {column}")


def _get_asset_check_value(column: DefsColumn, asset_check: DgAssetCheckMetadata) -> Optional[str]:
    if column == DefsColumn.KEY:
        return asset_check.key
    elif column == DefsColumn.DEPS:
        return "\n".join(asset_check.additional_deps)
    elif column == DefsColumn.DESCRIPTION:
        return asset_check.description
    else:
        raise ValueError(f"Invalid column: {column}")


def _get_job_value(column: DefsColumn, job: DgJobMetadata) -> Optional[str]:
    if column == DefsColumn.KEY:
        return job.name
    elif column == DefsColumn.DESCRIPTION:
        return job.description
    else:
        raise ValueError(f"Invalid column: {column}")


def _get_resource_value(column: DefsColumn, resource: DgResourceMetadata) -> Optional[str]:
    if column == DefsColumn.KEY:
        return resource.name
    else:
        raise ValueError(f"Invalid column: {column}")


def _get_schedule_value(column: DefsColumn, schedule: DgScheduleMetadata) -> Optional[str]:
    if column == DefsColumn.KEY:
        return schedule.name
    elif column == DefsColumn.CRON:
        return schedule.cron_schedule
    else:
        raise ValueError(f"Invalid column: {column}")


def _get_sensor_value(column: DefsColumn, sensor: DgSensorMetadata) -> Optional[str]:
    if column == DefsColumn.KEY:
        return sensor.name
    else:
        raise ValueError(f"Invalid column: {column}")


GET_VALUE_BY_DEFS_TYPE = {
    DefsType.ASSET: _get_asset_value,
    DefsType.ASSET_CHECK: _get_asset_check_value,
    DefsType.JOB: _get_job_value,
    DefsType.RESOURCE: _get_resource_value,
    DefsType.SCHEDULE: _get_schedule_value,
    DefsType.SENSOR: _get_sensor_value,
}


def _get_value(column: DefsColumn, defs_type: DefsType, defn: Any) -> Optional[Text]:
    raw_value = GET_VALUE_BY_DEFS_TYPE[defs_type](column, defn)
    value = Text(raw_value) if raw_value else None
    if value and column in _TRUNCATED_COLUMN_WIDTHS:
        value.truncate(max_width=_TRUNCATED_COLUMN_WIDTHS[column], overflow="ellipsis")
    return value


def _get_table(columns: Sequence[DefsColumn], defs_type: DefsType, defs: Sequence[Any]) -> "Table":
    columns_to_display = [column for column in columns if _supports_column(column, defs_type)]
    table = DagsterInnerTable(
        [column.value.replace("_", " ").capitalize() for column in columns_to_display]
    )
    table.columns[-1].max_width = 100

    for column_type, table_column in zip(columns_to_display, table.columns):
        if column_type in _TRUNCATED_COLUMN_WIDTHS:
            table_column.max_width = _TRUNCATED_COLUMN_WIDTHS[column_type]

    for defn in sorted(defs, key=lambda x: str(_get_value(DefsColumn.KEY, defs_type, x))):
        table.add_row(
            *(_get_value(column, defs_type, defn) for column in columns_to_display),
        )
    return table


@list_group.command(name="defs", aliases=["def"], cls=DgClickCommand)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="Output as JSON instead of a table.",
)
@click.option(
    "--path",
    "-p",
    type=click.Path(
        resolve_path=True,
        path_type=Path,
    ),
    help="Path to the definitions to list.",
)
@click.option(
    "--assets",
    "-a",
    help="Asset selection to list.",
)
@click.option(
    "--columns",
    "-c",
    multiple=True,
    help="Columns to display. Either a comma-separated list of column names, or multiple "
    "invocations of the flag. Available columns: "
    + ", ".join(column.value for column in DefsColumn),
)
@dg_global_options
@dg_path_options
@cli_telemetry_wrapper
def list_defs_command(
    output_json: bool,
    target_path: Path,
    path: Optional[Path],
    assets: Optional[str],
    columns: Optional[Sequence[str]],
    **global_options: object,
) -> None:
    """List registered Dagster definitions in the current project environment."""
    from rich.console import Console
    from rich.table import Table

    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_project_environment(target_path, cli_config)

    from dagster.components.list import list_definitions

    if columns:
        if len(columns) == 1 and "," in columns[0]:
            columns = columns[0].split(",")
        defs_columns = [_defs_column_from_str(column.lower()) for column in columns]
        if DefsColumn.KEY not in defs_columns:
            defs_columns = [DefsColumn.KEY] + defs_columns
    else:
        defs_columns = DEFAULT_COLUMNS

    # capture stdout during the definitions load so it doesn't pollute the structured output
    with capture_stdout(), disable_dagster_warnings():
        definitions = list_definitions(
            dg_context=dg_context,
            path=path,
            asset_selection=assets,
        )

    # JSON
    if output_json:  # pass it straight through
        if columns:
            raise click.UsageError("Cannot use --columns with --json")

        click.echo(json.dumps(definitions.to_dict(), indent=4))

    # TABLE
    else:
        if definitions.is_empty:
            click.echo("No definitions are defined for this project.")
            return

        console = Console()

        table = Table(border_style="dim")
        table.add_column("Section", style="bold")
        table.add_column("Definitions")

        if definitions.assets:
            table.add_row("Assets", _get_table(defs_columns, DefsType.ASSET, definitions.assets))
        if definitions.asset_checks:
            table.add_row(
                "Asset Checks",
                _get_table(defs_columns, DefsType.ASSET_CHECK, definitions.asset_checks),
            )
        if definitions.jobs:
            table.add_row("Jobs", _get_table(defs_columns, DefsType.JOB, definitions.jobs))
        if definitions.schedules:
            table.add_row(
                "Schedules", _get_table(defs_columns, DefsType.SCHEDULE, definitions.schedules)
            )
        if definitions.sensors:
            table.add_row("Sensors", _get_table(defs_columns, DefsType.SENSOR, definitions.sensors))
        if definitions.resources:
            table.add_row(
                "Resources", _get_table(defs_columns, DefsType.RESOURCE, definitions.resources)
            )

        console.print(table)


# ########################
# ##### ENVIRONMENT
# ########################


@dataclass
class DagsterPlusScopesForVariable:
    has_full_value: bool
    has_branch_value: bool
    has_local_value: bool


def _get_dagster_plus_keys(
    location_name: str, env_var_keys: set[str]
) -> Optional[Mapping[str, DagsterPlusScopesForVariable]]:
    """Retrieves the set Dagster Plus keys for the given location name, if Plus is configured, otherwise returns None."""
    if not DagsterPlusCliConfig.exists():
        return None
    config = DagsterPlusCliConfig.get()
    if not config.organization:
        return None

    scopes_for_key = defaultdict(lambda: DagsterPlusScopesForVariable(False, False, False))
    gql_client = DagsterPlusGraphQLClient.from_config(config)

    secrets_by_location = gql_client.execute(
        gql.GET_SECRETS_FOR_SCOPES_QUERY_NO_VALUE,
        {
            "locationName": location_name,
            "scopes": {
                "fullDeploymentScope": True,
                "allBranchDeploymentsScope": True,
                "localDeploymentScope": True,
            },
        },
    )["secretsOrError"]["secrets"]

    for secret in secrets_by_location:
        key = secret["secretName"]
        if key in env_var_keys:
            if secret["fullDeploymentScope"]:
                scopes_for_key[key].has_full_value = True
            if secret["allBranchDeploymentsScope"]:
                scopes_for_key[key].has_branch_value = True
            if secret["localDeploymentScope"]:
                scopes_for_key[key].has_local_value = True
    return scopes_for_key


@list_group.command(name="envs", aliases=["env"], cls=DgClickCommand)
@dg_path_options
@dg_global_options
@cli_telemetry_wrapper
def list_env_command(target_path: Path, **global_options: object) -> None:
    """List environment variables from the .env file of the current project."""
    from rich.console import Console

    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_project_environment(target_path, cli_config)

    env = ProjectEnvVars.from_ctx(dg_context)
    used_env_vars = get_project_specified_env_vars(dg_context)

    if not env.values and not used_env_vars:
        click.echo("No environment variables are defined for this project.")
        return

    env_var_keys = env.values.keys() | used_env_vars.keys()
    plus_keys = _get_dagster_plus_keys(dg_context.project_name, env_var_keys)

    table = DagsterOuterTable([])
    table.add_column("Env Var")
    table.add_column("Value")
    table.add_column("Components")
    if plus_keys is not None:
        table.add_column("Dev")
        table.add_column("Branch")
        table.add_column("Full")

    for key in sorted(env_var_keys):
        components = used_env_vars.get(key, [])
        table.add_row(
            key,
            "✓" if key in env.values else "",
            ", ".join(str(path) for path in components),
            *(
                [
                    "✓" if plus_keys[key].has_local_value else "",
                    "✓" if plus_keys[key].has_branch_value else "",
                    "✓" if plus_keys[key].has_full_value else "",
                ]
                if plus_keys is not None
                else []
            ),
        )

    console = Console()
    console.print(table)


@list_group.command(name="component-tree", aliases=["tree"], cls=DgClickCommand)
@click.option(
    "--output-file",
    help="Write to file instead of stdout. If not specified, will write to stdout.",
)
@dg_path_options
@dg_global_options
@cli_telemetry_wrapper
def list_component_tree_command(
    target_path: Path,
    output_file: Optional[str],
    **other_opts: object,
) -> None:
    cli_config = normalize_cli_config(other_opts, click.get_current_context())
    dg_context = DgContext.for_project_environment(target_path, cli_config)

    from dagster.components.core.component_tree import ComponentTree

    tree = ComponentTree.for_project(dg_context.root_path)
    output = tree.to_string_representation(hide_plain_defs=True)

    if output_file:
        click.echo("[dagster-components] Writing to file " + output_file)
        Path(output_file).write_text(output)
    else:
        click.echo(output)
