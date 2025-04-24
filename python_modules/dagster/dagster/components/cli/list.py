import json
import logging
import sys
from pathlib import Path
from traceback import TracebackException
from typing import Literal, Optional, Union

import click
from dagster_shared.error import SerializableErrorInfo, remove_system_frames_from_error
from dagster_shared.serdes.objects import PluginObjectKey
from dagster_shared.serdes.objects.definition_metadata import (
    DgAssetCheckMetadata,
    DgAssetMetadata,
    DgDefinitionMetadata,
    DgJobMetadata,
    DgScheduleMetadata,
    DgSensorMetadata,
)
from dagster_shared.serdes.objects.package_entry import PluginManifest
from dagster_shared.serdes.serdes import serialize_value
from pydantic import ConfigDict, TypeAdapter, create_model

from dagster._cli.utils import assert_no_remaining_opts, get_possibly_temporary_instance_for_cli
from dagster._cli.workspace.cli_target import (
    PythonPointerOpts,
    get_repository_python_origin_from_cli_opts,
    python_pointer_options,
)
from dagster._core.definitions.asset_job import is_reserved_asset_job_name
from dagster._utils.error import serializable_error_info_from_exc_info
from dagster._utils.hosted_user_process import recon_repository_from_origin
from dagster.components.component.component import Component
from dagster.components.core.defs_module import ComponentRequirementsModel
from dagster.components.core.package_entry import (
    ComponentsEntryPointLoadError,
    discover_entry_point_package_objects,
    discover_package_objects,
    get_plugin_entry_points,
)
from dagster.components.core.snapshot import get_package_entry_snap


@click.group(name="list")
def list_cli():
    """Commands for listing Dagster components and related entities."""


@list_cli.command(name="plugins")
@click.option("--entry-points/--no-entry-points", is_flag=True, default=True)
@click.argument("extra_modules", nargs=-1, type=str)
def list_plugins_command(entry_points: bool, extra_modules: tuple[str, ...]) -> None:
    """List registered plugin objects."""
    modules = [*(ep.value for ep in get_plugin_entry_points()), *extra_modules]
    try:
        plugin_objects = _load_plugin_objects(entry_points, extra_modules)
        object_snaps = [get_package_entry_snap(key, obj) for key, obj in plugin_objects.items()]
        output = PluginManifest(
            modules=modules,
            objects=object_snaps,
        )
    except ComponentsEntryPointLoadError as e:
        tb = TracebackException.from_exception(e)
        output = SerializableErrorInfo.from_traceback(tb)

    click.echo(serialize_value(output))


@list_cli.command(name="all-components-schema")
@click.option("--entry-points/--no-entry-points", is_flag=True, default=True)
@click.argument("extra_modules", nargs=-1, type=str)
def list_all_components_schema_command(entry_points: bool, extra_modules: tuple[str, ...]) -> None:
    """Builds a JSON schema which ORs the schema for a component
    file for all component types available in the current code location.
    """
    component_types = _load_component_types(entry_points, extra_modules)

    model_cls_list = []
    for key in sorted(component_types.keys(), key=lambda k: k.to_typename()):
        component_type = component_types[key]
        # Create ComponentFileModel schema for each type
        model_cls = component_type.get_model_cls()
        key_string = key.to_typename()
        if model_cls:
            model_cls_list.append(
                create_model(
                    key.name,
                    type=(Literal[key_string], key_string),
                    attributes=(model_cls, None),
                    requirements=(Optional[ComponentRequirementsModel], None),
                    __config__=ConfigDict(extra="forbid"),
                )
            )
    union_type = Union[tuple(model_cls_list)]  # type: ignore
    click.echo(json.dumps(TypeAdapter(union_type).json_schema()))


@list_cli.command(name="definitions")
@python_pointer_options
@click.option(
    "--location", "-l", help="Name of the code location, can be used to scope environment variables"
)
@click.option(
    "--output-file",
    help="Write to file instead of stdout. If not specified, will write to stdout.",
)
@click.pass_context
def list_definitions_command(
    ctx: click.Context,
    location: Optional[str],
    output_file: Optional[str],
    **other_opts: object,
) -> None:
    """List Dagster definitions."""
    python_pointer_opts = PythonPointerOpts.extract_from_cli_options(other_opts)
    assert_no_remaining_opts(other_opts)

    with get_possibly_temporary_instance_for_cli(
        "``dagster-components definitions list``"
    ) as instance:
        instance.inject_env_vars(location)

        logger = logging.getLogger("dagster")

        removed_system_frame_hint = (
            lambda is_first_hidden_frame,
            i: f"  [{i} dagster system frames hidden, run dg check defs --verbose to see the full stack trace]\n"
            if is_first_hidden_frame
            else f"  [{i} dagster system frames hidden]\n"
        )

        try:
            repository_origin = get_repository_python_origin_from_cli_opts(python_pointer_opts)
            recon_repo = recon_repository_from_origin(repository_origin)
            repo_def = recon_repo.get_definition()
        except Exception:
            underlying_error = remove_system_frames_from_error(
                serializable_error_info_from_exc_info(sys.exc_info()),
                build_system_frame_removed_hint=removed_system_frame_hint,
            )

            logger.error(f"Loading location {location} failed:\n\n{underlying_error.to_string()}")
            sys.exit(1)

        all_defs: list[DgDefinitionMetadata] = []

        asset_graph = repo_def.asset_graph
        for key in sorted(
            list(asset_graph.get_all_asset_keys()), key=lambda key: key.to_user_string()
        ):
            node = asset_graph.get(key)
            all_defs.append(
                DgAssetMetadata(
                    key=key.to_user_string(),
                    deps=sorted([k.to_user_string() for k in node.parent_keys]),
                    group=node.group_name,
                    kinds=sorted(list(node.kinds)),
                    description=node.description,
                    automation_condition=node.automation_condition.get_label()
                    if node.automation_condition
                    else None,
                )
            )
        for key in asset_graph.asset_check_keys:
            node = asset_graph.get(key)
            all_defs.append(
                DgAssetCheckMetadata(
                    key=key.to_user_string(),
                    asset_key=key.asset_key.to_user_string(),
                    name=key.name,
                    additional_deps=sorted([k.to_user_string() for k in node.parent_entity_keys]),
                    description=node.description,
                )
            )
        for job in repo_def.get_all_jobs():
            if not is_reserved_asset_job_name(job.name):
                all_defs.append(DgJobMetadata(name=job.name))
        for schedule in repo_def.schedule_defs:
            schedule_str = (
                schedule.cron_schedule
                if isinstance(schedule.cron_schedule, str)
                else ", ".join(schedule.cron_schedule)
            )
            all_defs.append(
                DgScheduleMetadata(
                    name=schedule.name,
                    cron_schedule=schedule_str,
                )
            )
        for sensor in repo_def.sensor_defs:
            all_defs.append(DgSensorMetadata(name=sensor.name))

        output = serialize_value(all_defs)
        if output_file:
            click.echo("[dagster-components] Writing to file " + output_file)
            Path(output_file).write_text(output)
        else:
            click.echo(output)


# ########################
# ##### HELPERS
# ########################


def _load_plugin_objects(
    entry_points: bool, extra_modules: tuple[str, ...]
) -> dict[PluginObjectKey, object]:
    objects = {}
    if entry_points:
        objects.update(discover_entry_point_package_objects())
    if extra_modules:
        objects.update(discover_package_objects(extra_modules))
    return objects


def _load_component_types(
    entry_points: bool, extra_modules: tuple[str, ...]
) -> dict[PluginObjectKey, type[Component]]:
    return {
        key: obj
        for key, obj in _load_plugin_objects(entry_points, extra_modules).items()
        if isinstance(obj, type) and issubclass(obj, Component)
    }
