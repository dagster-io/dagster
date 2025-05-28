import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import click
from dagster_dg_core.component import RemotePluginRegistry
from dagster_dg_core.config import normalize_cli_config
from dagster_dg_core.context import DgContext
from dagster_dg_core.env import ProjectEnvVars, get_project_specified_env_vars
from dagster_dg_core.shared_options import dg_global_options, dg_path_options
from dagster_dg_core.utils import (
    DgClickCommand,
    DgClickGroup,
    capture_stdout,
    validate_dagster_availability,
)
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.record import as_dict
from dagster_shared.serdes import deserialize_value
from dagster_shared.serdes.errors import DeserializationError
from dagster_shared.serdes.objects.definition_metadata import (
    DgAssetCheckMetadata,
    DgAssetMetadata,
    DgDefinitionMetadata,
    DgJobMetadata,
    DgResourceMetadata,
    DgScheduleMetadata,
    DgSensorMetadata,
)
from packaging.version import Version
from rich.console import Console

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
    path: Path, package: Optional[str], output_json: bool, **global_options: object
) -> None:
    """List all available Dagster component types in the current Python environment."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_defined_registry_environment(path, cli_config)
    registry = RemotePluginRegistry.from_dg_context(dg_context)

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


@list_group.command(name="plugin-modules", aliases=["plugin-module"], cls=DgClickCommand)
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
def list_plugin_modules_command(
    output_json: bool,
    path: Path,
    **global_options: object,
) -> None:
    """List dg plugins and their corresponding objects in the current Python environment."""
    from rich.console import Console

    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_defined_registry_environment(path, cli_config)
    registry = RemotePluginRegistry.from_dg_context(dg_context)

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


def _get_assets_table(assets: Sequence[DgAssetMetadata]) -> "Table":
    from rich.text import Text

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


def _get_asset_checks_table(asset_checks: Sequence[DgAssetCheckMetadata]) -> "Table":
    from rich.text import Text

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


def _get_jobs_table(jobs: Sequence[DgJobMetadata]) -> "Table":
    table = DagsterInnerTable(["Name"])

    for job in sorted(jobs, key=lambda x: x.name):
        table.add_row(job.name)
    return table


def _get_resources_table(resources: Sequence[DgResourceMetadata]) -> "Table":
    table = DagsterInnerTable(["Name", "Type"])

    for resource in sorted(resources, key=lambda x: x.name):
        table.add_row(resource.name, resource.type)
    return table


def _get_schedules_table(schedules: Sequence[DgScheduleMetadata]) -> "Table":
    table = DagsterInnerTable(["Name", "Cron schedule"])

    for schedule in sorted(schedules, key=lambda x: x.name):
        table.add_row(schedule.name, schedule.cron_schedule)
    return table


def _get_sensors_table(sensors: Sequence[DgSensorMetadata]) -> "Table":
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
    from rich.console import Console
    from rich.table import Table

    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_project_environment(path, cli_config)

    validate_dagster_availability()

    from dagster.components.cli.list import list_definitions_impl

    # capture stdout during the definitions load so it doesn't pollute the structured output
    with capture_stdout():
        definitions = list_definitions_impl(
            location=dg_context.code_location_name,
            module_name=dg_context.code_location_target_module_name,
        )

    # JSON
    if output_json:  # pass it straight through
        json_output = [as_dict(defn) for defn in definitions]
        click.echo(json.dumps(json_output, indent=4))

    # TABLE
    else:
        assets = [item for item in definitions if isinstance(item, DgAssetMetadata)]
        asset_checks = [item for item in definitions if isinstance(item, DgAssetCheckMetadata)]
        jobs = [item for item in definitions if isinstance(item, DgJobMetadata)]
        resources = [item for item in definitions if isinstance(item, DgResourceMetadata)]
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
        if resources:
            table.add_row("Resources", _get_resources_table(resources))

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
def list_env_command(path: Path, **global_options: object) -> None:
    """List environment variables from the .env file of the current project."""
    from rich.console import Console

    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_project_environment(path, cli_config)

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
