from typing import Dict, Mapping, Optional, Union

from dagster import (
    AssetsDefinition,
    AssetSpec,
    AssetKey,
    Definitions,
    _check as check,
    SourceAsset,
)

from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition
from dagster_airlift.utils import map_to_dag, map_to_task


class TaskDefs:
    def __init__(self, task_id: str, defs: Definitions):
        self.task_id = task_id
        self.defs = defs


def map_all_specs_to_task(defs: Definitions, dag_id: str, task_id: str) -> Definitions:
    return Definitions(
        assets=[
            # Right now we make assumptions that we only support AssetSpec and AssetsDefinition
            # in orchesrated_defs.
            # https://linear.app/dagster-labs/issue/FOU-369/support-cacheableassetsdefinition-and-sourceasset-in-airlift
            assets_def_with_task_map(
                _coerce_def_or_spec(asset),
                dag_id,
                task_id,
            )
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


def spec_with_tags(spec: AssetSpec, tags: Mapping[str, str]) -> "AssetSpec":
    return spec._replace(tags={**spec.tags, **tags})

def _coerce_def_or_spec(asset: Union[AssetsDefinition, AssetSpec, CacheableAssetsDefinition, SourceAsset]) -> Union[AssetSpec, AssetsDefinition]:
    return check.inst(
                    asset,
                    (AssetSpec, AssetsDefinition),
                    "Only supports AssetSpec and AssetsDefinition right now",
                )

def assets_def_with_task_map(
    assets_def: Union[AssetsDefinition, AssetSpec], dag_id: str, task_id: str
) -> Union[AssetsDefinition, AssetSpec]:
    return (
        assets_def.map_asset_specs(
            lambda spec: map_to_task(spec=spec, dag_id=dag_id, task_id=task_id)
        )
        if isinstance(assets_def, AssetsDefinition)
        else map_to_task(spec=assets_def, dag_id=dag_id, task_id=task_id)
    )


def dag_defs(dag_id: str, *defs: TaskDefs, spec: Optional[AssetSpec] = None) -> Definitions:
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
            task_defs("task_one", Definitions(assets=[AssetSpec(key="asset_one"]))),
            task_defs("task_two", Definitions(assets=[AssetSpec(key="asset_two"), AssetSpec(key="asset_three")])),
        )
    """
    dag_spec = map_to_dag(spec=spec, dag_id=dag_id) if spec else None
    defs_to_merge = []
    for task_def in defs:
        defs_to_merge.append(
            map_all_specs_to_task(
                defs=task_def.defs,
                dag_id=dag_id,
                task_id=task_def.task_id,
            )
        )
    return attempt_merge_dupes(Definitions.merge(*defs_to_merge, Definitions(assets=[dag_spec] if dag_spec else None)))

def attempt_merge_dupes(defs: Definitions) -> Definitions:
    """It's possible that the same asset has been mapped to multiple tasks in the same DAG.
    If possible, dedupe the asset specs by merging the metadata of the asset specs.
    """
    asset_per_key: Dict[AssetKey, Union[AssetSpec, AssetsDefinition]] = {}
    if not defs.assets:
        return defs
    for asset in defs.assets:
        # This is gonna get gross. The equality check here is going to be a bit complicated. 
        ...
            
    return Definitions(
        assets=asset_per_key.values(),
        resources=defs.resources,
        sensors=defs.sensors,
        schedules=defs.schedules,
        jobs=defs.jobs,
        loggers=defs.loggers,
        executor=defs.executor,
        asset_checks=defs.asset_checks,
    )

def task_defs(task_id, defs: Definitions) -> TaskDefs:
    """Associate a set of definitions with a particular task in Airflow that is being tracked
    by Airlift tooling.
    """
    return TaskDefs(task_id, defs)
