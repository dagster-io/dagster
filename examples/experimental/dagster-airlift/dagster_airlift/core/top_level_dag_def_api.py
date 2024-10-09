from typing import Any, Dict, Iterable, Mapping, Sequence, Union

from dagster import (
    AssetsDefinition,
    AssetSpec,
    Definitions,
    _check as check,
)

from dagster_airlift.core.utils import metadata_for_task_mapping


class TaskDefs:
    def __init__(self, task_id: str, defs: Definitions):
        self.task_id = task_id
        self.defs = defs


def apply_metadata_to_assets(
    assets: Iterable[Union[AssetsDefinition, AssetSpec]], metadata: Dict[str, Any]
) -> Sequence[Union[AssetsDefinition, AssetSpec]]:
    return [assets_def_with_af_metadata(asset, metadata) for asset in assets]


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


def spec_with_metadata(spec: AssetSpec, metadata: Mapping[str, Any]) -> "AssetSpec":
    return spec._replace(metadata={**spec.metadata, **metadata})


def assets_def_with_af_metadata(
    assets_def: Union[AssetsDefinition, AssetSpec], metadata: Mapping[str, str]
) -> Union[AssetsDefinition, AssetSpec]:
    return (
        assets_def.map_asset_specs(lambda spec: spec_with_metadata(spec, metadata))
        if isinstance(assets_def, AssetsDefinition)
        else spec_with_metadata(assets_def, metadata)
    )


def assets_with_task_mappings(
    dag_id: str, task_mappings: Mapping[str, Iterable[Union[AssetsDefinition, AssetSpec]]]
) -> Sequence[Union[AssetsDefinition, AssetSpec]]:
    """Modify assets to be associated with a particular task in Airlift tooling.

    Used in concert with `build_defs_from_airflow_instance` to observe an airflow
    instance to monitor the tasks that are associated with the assets and
    keep their materialization histories up to date.

    Concretely this adds metadata to all asset specs in the provided definitions
    with the provided dag_id and task_id. The dag_id comes from the dag_id argument;
    the task_id comes from the key of the provided task_mappings dictionary.
    There is a single metadata key "airlift/task_mapping" that is used to store
    this information. It is a list of dictionaries with keys "dag_id" and "task_id".

    Example:
    .. code-block:: python
        from dagster import AssetSpec, Definitions, asset
        from dagster_airlift.core import assets_with_task_mappings

        @asset
        def asset_one() -> None: ...

        defs = Definitions(
            assets=assets_with_task_mappings(
                dag_id="dag_one",
                task_mappings={
                    "task_one": [asset_one],
                    "task_two": [AssetSpec(key="asset_two"), AssetSpec(key="asset_three")],
                },
            )
        )
    """
    assets_list = []
    for task_id, assets in task_mappings.items():
        assets_list.extend(
            apply_metadata_to_assets(
                assets,
                metadata_for_task_mapping(task_id=task_id, dag_id=dag_id),
            )
        )
    return assets_list


def dag_defs(dag_id: str, *defs: TaskDefs) -> Definitions:
    """Construct a Dagster :py:class:`Definitions` object with definitions
    associated with a particular Dag in Airflow that is being tracked by Airlift tooling.

    Concretely this adds metadata to all asset specs in the provided definitions
    with the provided dag_id and task_id. There is a single metadata key
    "airlift/task_mapping" that is used to store this information. It is a list of
    dictionaries with keys "dag_id" and "task_id".

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
                metadata=metadata_for_task_mapping(task_id=task_def.task_id, dag_id=dag_id),
            )
        )
    return Definitions.merge(*defs_to_merge)


def task_defs(task_id, defs: Definitions) -> TaskDefs:
    """Associate a set of definitions with a particular task in Airflow that is being tracked
    by Airlift tooling.
    """
    return TaskDefs(task_id, defs)
