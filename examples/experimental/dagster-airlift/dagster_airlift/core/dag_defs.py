from typing import Any, Dict, Mapping, Sequence, Union

from dagster import (
    AssetsDefinition,
    AssetSpec,
    Definitions,
    JsonMetadataValue,
    SourceAsset,
    _check as check,
    external_asset_from_spec,
)
from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition
from dagster._core.definitions.external_asset import create_external_asset_from_source_asset

from dagster_airlift.constants import AIRFLOW_COUPLING_METADATA_KEY


class TaskDefs:
    def __init__(self, task_id: str, defs: Definitions):
        self.task_id = task_id
        self.defs = defs


def apply_metadata_to_all_specs(defs: Definitions, metadata: Dict[str, Any]) -> Definitions:
    return Definitions(
        assets=[
            # Right now we make assumptions that we only support AssetSpec and AssetsDefinition
            # in orchesrated_defs.
            # https://linear.app/dagster-labs/issue/FOU-369/support-cacheableassetsdefinition-and-sourceasset-in-airlift
            assets_def_with_af_metadata(asset, metadata)
            for asset in (defs.assets or [])
        ],
        resources=defs.resources,
        sensors=defs.sensors,
        schedules=defs.schedules,
        jobs=defs.jobs,
        loggers=defs.loggers,
        executor=defs.executor,
        asset_checks=defs.asset_checks,
    )


def spec_with_metadata(spec: AssetSpec, metadata: Mapping[str, str]) -> "AssetSpec":
    return spec._replace(metadata={**spec.metadata, **metadata})


def assets_def_with_af_metadata(
    asset: Union[AssetsDefinition, AssetSpec, CacheableAssetsDefinition, SourceAsset],
    metadata: Mapping[str, str],
) -> Union[AssetsDefinition, AssetSpec, CacheableAssetsDefinition]:
    if isinstance(asset, CacheableAssetsDefinition):
        return asset.with_attributes_for_all(
            group_name=None,
            freshness_policy=None,
            auto_materialize_policy=None,
            backfill_policy=None,
            metadata=metadata,
        )
    elif isinstance(asset, SourceAsset):
        asset = create_external_asset_from_source_asset(asset)

    return (
        asset.map_asset_specs(lambda spec: spec_with_metadata(spec, metadata))
        if isinstance(asset, AssetsDefinition)
        else spec_with_metadata(asset, metadata)
    )


class RefToDefs:
    def __init__(self, task_id: str, key: str):
        self.task_id = task_id
        self.key = key


class SharedSentinel:
    def __init__(self, key: str):
        self.key = key


def mark_as_shared(key: str) -> SharedSentinel:
    return SharedSentinel(key)


class DagDefs:
    def __init__(self, dag_id: str, task_defs: Dict[str, Union[TaskDefs, RefToDefs]]):
        self.task_defs = task_defs
        self.dag_id = dag_id

    def to_defs(self) -> Definitions:
        return Definitions.merge(
            *list(
                apply_metadata_to_all_specs(
                    defs=task_def_set.defs,
                    metadata={
                        AIRFLOW_COUPLING_METADATA_KEY: JsonMetadataValue(
                            [(self.dag_id, task_def_set.task_id)]
                        )
                    },
                )
                for task_def_set in self.task_defs.values()
                if isinstance(task_def_set, TaskDefs)
            )
        )

    def get_tasks_referencing_key(self, key: str) -> Sequence[str]:
        return [
            task_id
            for task_id, task_defs in self.task_defs.items()
            if isinstance(task_defs, RefToDefs) and task_defs.key == key
        ]


def dag_defs(dag_id: str, defs: Sequence[Union[TaskDefs, RefToDefs]]) -> DagDefs:
    """Construct a Dagster :py:class:`Definitions` object with definitions
    associated with a particular Dag in Airflow that is being tracked by Airlift tooling.

    Concretely this adds metadata to all asset specs in the provided definitions
    with the provided dag_id and task_id. Dag id is tagged with the
    "airlift/dag_id" key and task id is tagged with the "airlift/task_id" key.

    Used in concert with :py:func:`task_defs`.

    Example:
    .. code-block:: python
        defs = dag_defs(
            "dag_one",
            [
                task_defs("task_one", Definitions(assets=[AssetSpec(key="asset_one"]))),
                task_defs("task_two", Definitions(assets=[AssetSpec(key="asset_two"), AssetSpec(key="asset_three")])),
            ],
        )
    """
    return DagDefs(dag_id, {task_def.task_id: task_def for task_def in defs})


def task_defs(task_id, defs: Union[Definitions, SharedSentinel]) -> Union[TaskDefs, RefToDefs]:
    """Associate a set of definitions with a particular task in Airflow that is being tracked
    by Airlift tooling.
    """
    return (
        TaskDefs(task_id, defs)
        if not isinstance(defs, SharedSentinel)
        else RefToDefs(task_id, defs.key)
    )


def resolve_defs(
    dag_defs: Sequence[Union[DagDefs, Definitions]], keyed_defs: Mapping[str, Definitions]
) -> Definitions:
    transformed_defs = []
    for key, defs in keyed_defs.items():
        dags_and_tasks = [
            (dag.dag_id, task_id)
            for dag in dag_defs
            if isinstance(dag, DagDefs)
            for task_id in dag.get_tasks_referencing_key(key)
        ]
        transformed_defs.append(
            apply_metadata_to_all_specs(
                defs=defs,
                metadata={AIRFLOW_COUPLING_METADATA_KEY: JsonMetadataValue(dags_and_tasks)},
            )
        )

    return coerce_specs_in_defs(
        Definitions.merge(
            *list(
                dag_def.to_defs() if isinstance(dag_def, DagDefs) else dag_def
                for dag_def in dag_defs
            ),
            *transformed_defs,
        )
    )


def coerce_specs_in_defs(defs: Definitions) -> Definitions:
    new_assets = []
    for asset in defs.assets or []:
        if isinstance(asset, (AssetsDefinition, CacheableAssetsDefinition, SourceAsset)):
            new_assets.append(asset)
        elif isinstance(asset, AssetSpec):
            new_assets.append(external_asset_from_spec(asset))
        else:
            check.failed(f"Unsupported asset type {type(asset)}")
    return Definitions(
        assets=new_assets,
        resources=defs.resources,
        sensors=defs.sensors,
        schedules=defs.schedules,
        jobs=defs.jobs,
        loggers=defs.loggers,
        executor=defs.executor,
        asset_checks=defs.asset_checks,
    )
