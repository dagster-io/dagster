from typing import Any, Mapping, Optional

from dagster import JsonMetadataValue
from dagster._core.definitions.metadata.metadata_value import UrlMetadataValue

from dagster_airlift.constants import MIGRATED_TAG
from dagster_airlift.core.airflow_instance import TaskInfo
from dagster_airlift.core.serialization.serialized_data import SerializedAssetKeyScopedAirflowData
from dagster_airlift.core.utils import airflow_kind_dict


def get_airflow_data_for_task_mapped_spec(
    task_info: TaskInfo,
    migration_state: Optional[bool],
) -> SerializedAssetKeyScopedAirflowData:
    tags = airflow_kind_dict() if not migration_state else {}
    if migration_state is not None:
        tags[MIGRATED_TAG] = str(bool(migration_state))
    return SerializedAssetKeyScopedAirflowData(
        additional_metadata=task_asset_metadata(task_info, migration_state),
        additional_tags=tags,
    )


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
