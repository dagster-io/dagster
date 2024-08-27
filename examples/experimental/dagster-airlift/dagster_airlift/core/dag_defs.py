from typing import Dict, Mapping, Union

from dagster import (
    AssetsDefinition,
    AssetSpec,
    Definitions,
    _check as check,
)
from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition
from dagster._core.definitions.source_asset import SourceAsset

from dagster_airlift.core.utils import DAG_ID_TAG, TASK_ID_TAG

from .spec_tags_cacheable_assets import SpecWithTagsCacheableAssetsDefinition, spec_with_tags


class TaskDefs:
    def __init__(self, task_id: str, defs: Definitions):
        self.task_id = task_id
        self.defs = defs


def apply_tags_to_all_specs(defs: Definitions, tags: Dict[str, str]) -> Definitions:
    return Definitions(
        assets=[assets_def_with_af_tags(asset, tags) for asset in (defs.assets or [])],
        resources=defs.resources,
        sensors=defs.sensors,
        schedules=defs.schedules,
        jobs=defs.jobs,
        loggers=defs.loggers,
        executor=defs.executor,
        asset_checks=defs.asset_checks,
    )


def source_asset_with_tags(source_asset: SourceAsset, tags: Mapping[str, str]) -> SourceAsset:
    return SourceAsset(
        key=source_asset.key,
        metadata=source_asset.raw_metadata,
        io_manager_key=source_asset.io_manager_key,
        io_manager_def=source_asset.io_manager_def,
        description=source_asset.description,
        partitions_def=source_asset.partitions_def,
        group_name=source_asset.group_name,
        resource_defs=source_asset.resource_defs,
        observe_fn=source_asset.observe_fn,
        auto_observe_interval_minutes=source_asset.auto_observe_interval_minutes,
        tags={**(source_asset.tags or {}), **tags},
        _required_resource_keys=source_asset._required_resource_keys,  # noqa
    )


def assets_def_with_af_tags(
    assets_def: Union[AssetsDefinition, AssetSpec, CacheableAssetsDefinition, SourceAsset],
    tags: Mapping[str, str],
) -> Union[AssetsDefinition, AssetSpec, CacheableAssetsDefinition, SourceAsset]:
    if isinstance(assets_def, AssetSpec):
        return spec_with_tags(assets_def, tags)
    if isinstance(assets_def, AssetsDefinition):
        return assets_def.map_asset_specs(lambda spec: spec_with_tags(spec, tags))
    if isinstance(assets_def, CacheableAssetsDefinition):
        return SpecWithTagsCacheableAssetsDefinition(assets_def, tags)
    if isinstance(assets_def, SourceAsset):
        return source_asset_with_tags(assets_def, tags)

    check.failed(f"Unexpected type {type(assets_def)}")


def dag_defs(dag_id: str, *defs: TaskDefs) -> Definitions:
    """Construct a Dagster :py:class:`Definitions` object with definitions
    associated with a particular Dag in Airflow that is being tracked by Airlift tooling.

    Concretely this adds tags to all asset specs in the provided definitions
    with the provided dag_id and task_id. Dag id is tagged with the
    "airlift/dag_id" key and task id is tagged with the "airlift/task_id" key.

    Used in concert with :py:func:`task_defs`.

    Example:
    .. code-block:: python
        defs = dag_defs(
            "dag_one",
            task_defs("task_one", Definitions(assets=[AssetSpec(key="asset_one"]))),
            task_defs("task_two", Definitions(assets=[AssetSpec(key="asset_two"), AssetSpec(key="asset_three")])),
        )
    """
    defs_to_merge = []
    for task_def in defs:
        defs_to_merge.append(
            apply_tags_to_all_specs(
                defs=task_def.defs,
                tags={DAG_ID_TAG: dag_id, TASK_ID_TAG: task_def.task_id},
            )
        )
    return Definitions.merge(*defs_to_merge)


def task_defs(task_id, defs: Definitions) -> TaskDefs:
    """Associate a set of definitions with a particular task in Airflow that is being tracked
    by Airlift tooling.
    """
    return TaskDefs(task_id, defs)
