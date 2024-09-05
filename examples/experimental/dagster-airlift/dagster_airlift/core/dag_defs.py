from typing import Any, Dict, Mapping, Union

from dagster import (
    AssetsDefinition,
    AssetSpec,
    Definitions,
    _check as check,
)

from dagster_airlift.constants import DAG_ID_METADATA_KEY, TASK_ID_METADATA_KEY


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
            assets_def_with_af_metadata(
                check.inst(
                    asset,
                    (AssetSpec, AssetsDefinition),
                    "Only supports AssetSpec and AssetsDefinition right now",
                ),
                metadata,
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


def spec_with_metadata(spec: AssetSpec, metadata: Mapping[str, str]) -> "AssetSpec":
    return spec._replace(metadata={**spec.metadata, **metadata})


def assets_def_with_af_metadata(
    assets_def: Union[AssetsDefinition, AssetSpec], metadata: Mapping[str, str]
) -> Union[AssetsDefinition, AssetSpec]:
    return (
        assets_def.map_asset_specs(lambda spec: spec_with_metadata(spec, metadata))
        if isinstance(assets_def, AssetsDefinition)
        else spec_with_metadata(assets_def, metadata)
    )


def dag_defs(dag_id: str, *defs: TaskDefs) -> Definitions:
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
    defs_to_merge = []
    for task_def in defs:
        defs_to_merge.append(
            apply_metadata_to_all_specs(
                defs=task_def.defs,
                metadata={DAG_ID_METADATA_KEY: dag_id, TASK_ID_METADATA_KEY: task_def.task_id},
            )
        )
    return Definitions.merge(*defs_to_merge)


def task_defs(task_id, defs: Definitions) -> TaskDefs:
    """Associate a set of definitions with a particular task in Airflow that is being tracked
    by Airlift tooling.
    """
    return TaskDefs(task_id, defs)
