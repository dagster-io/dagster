from typing import List, TypedDict, Union

from dagster import AssetsDefinition, AssetSpec

from dagster_airlift.constants import TASK_MAPPING_METADATA_KEY
from dagster_airlift.core import (
    build_defs_from_airflow_instance as build_defs_from_airflow_instance,
)
from dagster_airlift.core.dag_defs import spec_with_metadata


class TaskHandleDict(TypedDict):
    dag_id: str
    task_id: str


def targeted_by_multiple_tasks(
    asset: Union[AssetSpec, AssetsDefinition], task_handles: List[TaskHandleDict]
) -> Union[AssetSpec, AssetsDefinition]:
    """Given an asset or assets definition, return a new asset or assets definition with metadata
    that indicates that it is targeted by multiple airflow tasks. An example of this would
    be a separate weekly and daily dag that contains a task that targets a single asset.

    .. code-block:: python

    from dagster import Definitions, AssetSpec, asset
    from dagster_airlift import build_defs_from_airflow_instance, dag_defs, task_defs, targeted_by_multiple_tasks

    @asset
    def scheduled_twice(): ...

    defs = build_defs_from_airflow_instance(
        airflow_instance=airflow_instance
        defs=Definitions.merge(
            dag_defs(
                "other_dag",
                task_defs(
                    "task1",
                    Definitions(assets=[other_asset]),
                ),
            ),
            Definitions(
                assets=[
                    targeted_by_multiple_tasks(
                        scheduled_twice,
                        task_handles=[
                            {"dag_id": "weekly_dag", "task_id": "task1"},
                            {"dag_id": "daily_dag", "task_id": "task1"},
                        ],
                    )
                ]
            ),
        ),
    )
    """
    if isinstance(asset, AssetSpec):
        return spec_with_metadata(asset, {TASK_MAPPING_METADATA_KEY: task_handles})

    return asset.map_asset_specs(
        lambda spec: spec_with_metadata(spec, {TASK_MAPPING_METADATA_KEY: task_handles})
    )
