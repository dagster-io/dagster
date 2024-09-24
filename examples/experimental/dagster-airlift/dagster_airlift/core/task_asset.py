from typing import Any, List, Mapping, NamedTuple, Optional

from dagster import (
    AssetKey,
    JsonMetadataValue,
    _check as check,
)
from dagster._core.definitions.metadata.metadata_value import UrlMetadataValue
from dagster._record import record

from dagster_airlift.core.airflow_instance import TaskInfo
from dagster_airlift.core.serialization.serialized_data import SerializedAssetKeyScopedAirflowData
from dagster_airlift.core.utils import airflow_kind_dict


class TaskHandle(NamedTuple):
    dag_id: str
    task_id: str


@record
class FetchedAirflowTask:
    task_info: TaskInfo
    task_handle: TaskHandle
    migrated: Optional[bool]


@record
class AirflowTaskDagsterAssetEdge:
    asset_key: AssetKey
    fetched_airflow_task: FetchedAirflowTask


def get_airflow_data_for_task_mapped_spec(
    edges: List[AirflowTaskDagsterAssetEdge],
) -> SerializedAssetKeyScopedAirflowData:
    check.param_invariant(
        len(edges) == 1,
        "edges",
        "For now we constrain to 1:1 relationship between asset and task until we support multiple tasks in asset metadata",
    )
    migration_state = edges[0].fetched_airflow_task.migrated
    task_info = edges[0].fetched_airflow_task.task_info

    return SerializedAssetKeyScopedAirflowData(
        additional_metadata=task_asset_metadata(task_info, migration_state),
        additional_tags=tags_from_edges(edges),
    )


def tags_from_edges(edges: List[AirflowTaskDagsterAssetEdge]) -> Mapping[str, str]:
    all_not_migrated = all(not edge.fetched_airflow_task.migrated for edge in edges)
    return airflow_kind_dict() if all_not_migrated else {}


def task_asset_metadata(task_info: TaskInfo, migration_state: Optional[bool]) -> Mapping[str, Any]:
    task_level_metadata = {
        "Task Info (raw)": JsonMetadataValue(task_info.metadata),
        # In this case,
        "Dag ID": task_info.dag_id,
        "Link to DAG": UrlMetadataValue(task_info.dag_url),
    }
    task_level_metadata[
        "Computed in Task ID" if not migration_state else "Triggered by Task ID"
    ] = task_info.task_id
    return task_level_metadata
