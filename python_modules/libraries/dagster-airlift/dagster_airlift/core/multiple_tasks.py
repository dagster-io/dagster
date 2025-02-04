from collections.abc import Sequence
from typing import TypedDict, Union, cast

from dagster._annotations import beta
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions

from dagster_airlift.constants import TASK_MAPPING_METADATA_KEY
from dagster_airlift.core import (
    build_defs_from_airflow_instance as build_defs_from_airflow_instance,
)
from dagster_airlift.core.load_defs import replace_assets_in_defs
from dagster_airlift.core.top_level_dag_def_api import spec_with_metadata


@beta
class TaskHandleDict(TypedDict):
    dag_id: str
    task_id: str


@beta
def assets_with_multiple_task_mappings(
    assets: Sequence[Union[AssetSpec, AssetsDefinition]], task_handles: list[TaskHandleDict]
) -> Sequence[Union[AssetSpec, AssetsDefinition]]:
    """Given an asset or assets definition, return a new asset or assets definition with metadata
    that indicates that it is targeted by multiple airflow tasks. An example of this would
    be a separate weekly and daily dag that contains a task that targets a single asset.

    .. code-block:: python

        from dagster import Definitions, AssetSpec, asset
        from dagster_airlift import (
            build_defs_from_airflow_instance,
            targeted_by_multiple_tasks,
            assets_with_task_mappings,
        )

        # Asset maps to a single task.
        @asset
        def other_asset(): ...

        # Asset maps to a physical entity which is produced by two different airflow tasks.
        @asset
        def scheduled_twice(): ...

        defs = build_defs_from_airflow_instance(
            airflow_instance=airflow_instance,
            defs=Definitions(
                assets=[
                    *assets_with_task_mappings(
                        dag_id="other_dag",
                        task_mappings={
                            "task1": [other_asset]
                        },
                    ),
                    *assets_with_multiple_task_mappings(
                        assets=[scheduled_twice],
                        task_handles=[
                            {"dag_id": "weekly_dag", "task_id": "task1"},
                            {"dag_id": "daily_dag", "task_id": "task1"},
                        ],
                    ),
                ]
            ),
        )

    """
    return [
        asset.map_asset_specs(
            lambda spec: spec_with_metadata(spec, {TASK_MAPPING_METADATA_KEY: task_handles})
        )
        if isinstance(asset, AssetsDefinition)
        else spec_with_metadata(asset, {TASK_MAPPING_METADATA_KEY: task_handles})
        for asset in assets
    ]


def targeted_by_multiple_tasks(
    defs: Definitions, task_handles: list[TaskHandleDict]
) -> Definitions:
    return replace_assets_in_defs(
        defs,
        assets_with_multiple_task_mappings(
            cast(Sequence[Union[AssetSpec, AssetsDefinition]], defs.assets),
            task_handles=task_handles,
        ),
    )
