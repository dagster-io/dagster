from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Union

from dagster import (
    AssetsDefinition,
    AssetSpec,
    Definitions,
    _check as check,
)
from dagster._annotations import beta

from dagster_airlift.core.utils import metadata_for_dag_mapping, metadata_for_task_mapping


def apply_metadata_to_assets(
    assets: Iterable[Union[AssetsDefinition, AssetSpec]], metadata: dict[str, Any]
) -> Sequence[Union[AssetsDefinition, AssetSpec]]:
    return [assets_def_with_af_metadata(asset, metadata) for asset in assets]


def apply_metadata_to_all_specs(defs: Definitions, metadata: dict[str, Any]) -> Definitions:
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


@beta
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
    There is a single metadata key "airlift/task-mapping" that is used to store
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


@beta
def assets_with_dag_mappings(
    dag_mappings: Mapping[str, Iterable[Union[AssetsDefinition, AssetSpec]]],
) -> Sequence[Union[AssetsDefinition, AssetSpec]]:
    """Modify assets to be associated with a particular dag in Airlift tooling.

    Used in concert with `build_defs_from_airflow_instance` to observe an airflow
    instance to monitor the dags that are associated with the assets and
    keep their materialization histories up to date.

    In contrast with `assets_with_task_mappings`, which maps assets on a per-task basis, this is used in concert with
    `proxying_to_dagster` dag-level mappings where an entire dag is migrated at once.

    Concretely this adds metadata to all asset specs in the provided definitions
    with the provided dag_id. The dag_id comes from the key of the provided dag_mappings dictionary.
    There is a single metadata key "airlift/dag-mapping" that is used to store
    this information. It is a list of strings, where each string is a dag_id which the asset is associated with.

    Example:

    .. code-block:: python

        from dagster import AssetSpec, Definitions, asset
        from dagster_airlift.core import assets_with_dag_mappings

        @asset
        def asset_one() -> None: ...

        defs = Definitions(
            assets=assets_with_dag_mappings(
                dag_mappings={
                    "dag_one": [asset_one],
                    "dag_two": [AssetSpec(key="asset_two"), AssetSpec(key="asset_three")],
                },
            )
        )
    """
    assets_list = []
    for dag_id, assets in dag_mappings.items():
        assets_list.extend(
            apply_metadata_to_assets(
                assets,
                metadata_for_dag_mapping(dag_id=dag_id),
            )
        )
    return assets_list
