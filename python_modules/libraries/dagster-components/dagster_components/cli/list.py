import json
from typing import Any, Literal, Union

import click
from dagster._cli.utils import assert_no_remaining_opts
from dagster._cli.workspace.cli_target import (
    PythonPointerOpts,
    get_repository_python_origin_from_cli_opts,
    python_pointer_options,
)
from dagster._core.definitions.asset_job import is_reserved_asset_job_name
from dagster._utils.hosted_user_process import recon_repository_from_origin
from pydantic import ConfigDict, TypeAdapter, create_model

from dagster_components.core.component import (
    Component,
    ComponentTypeMetadata,
    discover_component_types,
    discover_entry_point_component_types,
)
from dagster_components.core.component_key import ComponentKey
from dagster_components.core.defs import (
    DgAssetMetadata,
    DgDefinitionMetadata,
    DgJobMetadata,
    DgScheduleMetadata,
    DgSensorMetadata,
)


@click.group(name="list")
def list_cli():
    """Commands for listing Dagster components and related entities."""


@list_cli.command(name="component-types")
@click.option("--entry-points/--no-entry-points", is_flag=True, default=True)
@click.argument("extra_modules", nargs=-1, type=str)
@click.pass_context
def list_component_types_command(
    ctx: click.Context, entry_points: bool, extra_modules: tuple[str, ...]
) -> None:
    """List registered Dagster components."""
    output: dict[str, Any] = {}
    component_types = _load_component_types(entry_points, extra_modules)
    for key in sorted(component_types.keys(), key=lambda k: k.to_typename()):
        output[key.to_typename()] = ComponentTypeMetadata(
            name=key.name,
            namespace=key.namespace,
            **component_types[key].get_metadata(),
        )
    click.echo(json.dumps(output))


@list_cli.command(name="all-components-schema")
@click.option("--entry-points/--no-entry-points", is_flag=True, default=True)
@click.argument("extra_modules", nargs=-1, type=str)
def list_all_components_schema_command(entry_points: bool, extra_modules: tuple[str, ...]) -> None:
    """Builds a JSON schema which ORs the schema for a component
    file for all component types available in the current code location.
    """
    component_types = _load_component_types(entry_points, extra_modules)

    schemas = []
    for key in sorted(component_types.keys(), key=lambda k: k.to_typename()):
        component_type = component_types[key]
        # Create ComponentFileModel schema for each type
        schema_type = component_type.get_schema()
        key_string = key.to_typename()
        if schema_type:
            schemas.append(
                create_model(
                    key.name,
                    type=(Literal[key_string], key_string),
                    attributes=(schema_type, None),
                    __config__=ConfigDict(extra="forbid"),
                )
            )
    union_type = Union[tuple(schemas)]  # type: ignore
    click.echo(json.dumps(TypeAdapter(union_type).json_schema()))


@list_cli.command(name="definitions")
@python_pointer_options
@click.pass_context
def list_definitions_command(ctx: click.Context, **other_opts: object) -> None:
    """List registered Dagster components."""
    python_pointer_opts = PythonPointerOpts.extract_from_cli_options(other_opts)
    assert_no_remaining_opts(other_opts)

    repository_origin = get_repository_python_origin_from_cli_opts(python_pointer_opts)
    recon_repo = recon_repository_from_origin(repository_origin)
    repo_def = recon_repo.get_definition()

    all_defs: list[DgDefinitionMetadata] = []

    asset_graph = repo_def.asset_graph
    for key in sorted(list(asset_graph.get_all_asset_keys()), key=lambda key: key.to_user_string()):
        node = asset_graph.get(key)
        all_defs.append(
            DgAssetMetadata(
                type="asset",
                key=key.to_user_string(),
                deps=sorted([k.to_user_string() for k in node.parent_keys]),
                group=node.group_name,
                kinds=sorted(list(node.kinds)),
                description=node.description,
                automation_condition=node.automation_condition.__name__
                if node.automation_condition
                else None,
            )
        )
    for job in repo_def.get_all_jobs():
        if not is_reserved_asset_job_name(job.name):
            all_defs.append(DgJobMetadata(type="job", name=job.name))
    for schedule in repo_def.schedule_defs:
        schedule_str = (
            schedule.cron_schedule
            if isinstance(schedule.cron_schedule, str)
            else ", ".join(schedule.cron_schedule)
        )
        all_defs.append(
            DgScheduleMetadata(
                type="schedule",
                name=schedule.name,
                cron_schedule=schedule_str,
            )
        )
    for sensor in repo_def.sensor_defs:
        all_defs.append(DgSensorMetadata(type="sensor", name=sensor.name))

    click.echo(json.dumps(all_defs))


# ########################
# ##### HELPERS
# ########################


def _load_component_types(
    entry_points: bool, extra_modules: tuple[str, ...]
) -> dict[ComponentKey, type[Component]]:
    component_types = {}
    if entry_points:
        component_types.update(discover_entry_point_component_types())
    if extra_modules:
        component_types.update(discover_component_types(extra_modules))
    return component_types
