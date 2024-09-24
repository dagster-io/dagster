from typing import Any, List, Mapping, NamedTuple, Optional

from dagster import JsonMetadataValue
from dagster._core.definitions.asset_spec import AssetSpec
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
class TasksToAssetMapping:
    """Represents a mapping between a Dagster asset and the tasks in Airflow
    that orchestrate. We support multiple tasks mapping to a single asset. (e.g. a daily and weekly DAG)
    So there can multiple tasks for single asset key.
    """

    asset: AssetSpec
    mapped_tasks: List[FetchedAirflowTask]


def get_airflow_data_for_task_mapped_spec(
    mapping: TasksToAssetMapping,
) -> SerializedAssetKeyScopedAirflowData:
    return SerializedAssetKeyScopedAirflowData(
        additional_metadata=task_asset_metadata(mapping),
        additional_tags=tags_from_mapping(mapping),
    )


def tags_from_mapping(mapping: TasksToAssetMapping) -> Mapping[str, str]:
    all_not_migrated = all(not task.migrated for task in mapping.mapped_tasks)
    # Only show the airflow kind if the asset is orchestrated exlusively by airflow
    return airflow_kind_dict() if all_not_migrated else {}


def task_asset_metadata(mapping: TasksToAssetMapping) -> Mapping[str, Any]:
    # Just grab first one for now
    fetched_task = mapping.mapped_tasks[0]
    task_info, migration_state = fetched_task.task_info, fetched_task.migrated
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
