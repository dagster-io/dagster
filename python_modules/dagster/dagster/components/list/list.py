import logging
import sys
from collections.abc import Sequence
from pathlib import Path
from traceback import TracebackException
from typing import Any, Literal, Optional, Union

import click
from dagster_dg_core.context import DgContext
from dagster_shared.cli import PythonPointerOpts
from dagster_shared.error import SerializableErrorInfo, remove_system_frames_from_error
from dagster_shared.serdes.objects import PluginObjectKey
from dagster_shared.serdes.objects.definition_metadata import (
    DgAssetCheckMetadata,
    DgAssetMetadata,
    DgDefinitionMetadata,
    DgJobMetadata,
    DgResourceMetadata,
    DgScheduleMetadata,
    DgSensorMetadata,
)
from dagster_shared.serdes.objects.package_entry import PluginManifest
from pydantic import ConfigDict, TypeAdapter, create_model

from dagster._cli.utils import get_possibly_temporary_instance_for_cli
from dagster._cli.workspace.cli_target import get_repository_python_origin_from_cli_opts
from dagster._config.pythonic_config.resource import get_resource_type_name
from dagster._core.definitions.asset_job import is_reserved_asset_job_name
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.repository_definition.repository_definition import (
    RepositoryDefinition,
)
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
from dagster.components.core.tree import ComponentTree


def list_plugins(
    entry_points: bool, extra_modules: Sequence[str]
) -> Union[PluginManifest, SerializableErrorInfo]:
    modules = [*(ep.value for ep in get_plugin_entry_points()), *extra_modules]
    try:
        plugin_objects = _load_plugin_objects(entry_points, extra_modules)
        object_snaps = [get_package_entry_snap(key, obj) for key, obj in plugin_objects.items()]
        return PluginManifest(
            modules=modules,
            objects=object_snaps,
        )
    except ComponentsEntryPointLoadError as e:
        tb = TracebackException.from_exception(e)
        return SerializableErrorInfo.from_traceback(tb)


def list_all_components_schema(
    entry_points: bool, extra_modules: tuple[str, ...]
) -> dict[str, Any]:
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
    return TypeAdapter(union_type).json_schema()


def _load_defs_at_path(dg_context: DgContext, path: Optional[Path]) -> RepositoryDefinition:
    """Attempts to load the component tree from the context project root, falling back to
    resolving the entire repository and using the attached component tree.
    """
    if not path:
        repository_origin = get_repository_python_origin_from_cli_opts(
            PythonPointerOpts.extract_from_cli_options(dict(dg_context.target_args))
        )
        recon_repo = recon_repository_from_origin(repository_origin)
        repo_def = recon_repo.get_definition()
        return repo_def

    tree = ComponentTree.load(dg_context.root_path)

    try:
        defs = tree.load_defs_at_path(path) if path else tree.load_defs()
    except Exception as e:
        path_text = f" at {path}" if path else ""
        raise click.ClickException(f"Unable to load definitions{path_text}: {e}") from e

    return defs.get_repository_def()


def list_definitions(
    dg_context: DgContext,
    path: Optional[Path] = None,
    asset_selection: Optional[str] = None,
) -> list[DgDefinitionMetadata]:
    with get_possibly_temporary_instance_for_cli() as instance:
        instance.inject_env_vars(dg_context.code_location_name)

        logger = logging.getLogger("dagster")

        removed_system_frame_hint = (
            lambda is_first_hidden_frame,
            i: f"  [{i} dagster system frames hidden, run dg check defs --verbose to see the full stack trace]\n"
            if is_first_hidden_frame
            else f"  [{i} dagster system frames hidden]\n"
        )

        try:
            repo_def = _load_defs_at_path(dg_context, path)
        except click.ClickException:
            raise
        except Exception:
            underlying_error = remove_system_frames_from_error(
                serializable_error_info_from_exc_info(sys.exc_info()),
                build_system_frame_removed_hint=removed_system_frame_hint,
            )

            logger.error(
                f"Loading location {dg_context.project_name} failed:\n\n{underlying_error.to_string()}"
            )
            sys.exit(1)

        all_defs: list[DgDefinitionMetadata] = []
        asset_graph = repo_def.asset_graph

        asset_selection_obj = (
            AssetSelection.from_string(asset_selection) if asset_selection else None
        )
        selected_assets = asset_selection_obj.resolve(asset_graph) if asset_selection_obj else None
        selected_checks = (
            asset_selection_obj.resolve_checks(asset_graph) if asset_selection_obj else None
        )
        for key in sorted(
            selected_assets or list(asset_graph.get_all_asset_keys()),
            key=lambda key: key.to_user_string(),
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
        for key in selected_checks if selected_checks is not None else asset_graph.asset_check_keys:
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
        # If we have an asset selection, we only want to return assets
        if asset_selection:
            return all_defs

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
        for name, resource in repo_def.get_top_level_resources().items():
            all_defs.append(DgResourceMetadata(name=name, type=get_resource_type_name(resource)))

        return all_defs


# ########################
# ##### HELPERS
# ########################


def _load_plugin_objects(
    entry_points: bool, extra_modules: Sequence[str]
) -> dict[PluginObjectKey, object]:
    objects = {}
    if entry_points:
        objects.update(discover_entry_point_package_objects())
    if extra_modules:
        objects.update(discover_package_objects(extra_modules))
    return objects


def _load_component_types(
    entry_points: bool, extra_modules: Sequence[str]
) -> dict[PluginObjectKey, type[Component]]:
    return {
        key: obj
        for key, obj in _load_plugin_objects(entry_points, extra_modules).items()
        if isinstance(obj, type) and issubclass(obj, Component)
    }
