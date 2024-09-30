from typing import Any, Callable, Iterable, List, Mapping, Sequence

from dagster import (
    AssetMaterialization,
    JsonMetadataValue,
    MarkdownMetadataValue,
    TimestampMetadataValue,
    _check as check,
)
from dagster._time import get_current_timestamp

from dagster_airlift.constants import EFFECTIVE_TIMESTAMP_METADATA_KEY
from dagster_airlift.core.airflow_defs_data import AirflowDefinitionsData
from dagster_airlift.core.airflow_instance import DagRun, TaskInstance

AirflowEventTranslationFn = Callable[
    [DagRun, Sequence[TaskInstance], AirflowDefinitionsData], Iterable[AssetMaterialization]
]


def get_asset_events(
    dag_run: DagRun, task_instances: Sequence[TaskInstance], airflow_data: AirflowDefinitionsData
) -> List[AssetMaterialization]:
    mats: List[AssetMaterialization] = []
    mats.extend(materializations_for_dag_run(dag_run, airflow_data))
    for task_run in task_instances:
        mats.extend(
            materializations_for_task_instance(
                airflow_data=airflow_data, dag_run=dag_run, task_instance=task_run
            )
        )
    return mats


def get_timestamp_from_materialization(mat: AssetMaterialization) -> float:
    return check.float_param(
        mat.metadata[EFFECTIVE_TIMESTAMP_METADATA_KEY].value, "Materialization Effective Timestamp"
    )


def materializations_for_dag_run(
    dag_run: DagRun, airflow_data: AirflowDefinitionsData
) -> Sequence[AssetMaterialization]:
    return [
        AssetMaterialization(
            asset_key=airflow_data.asset_key_for_dag(dag_run.dag_id),
            description=dag_run.note,
            metadata=get_dag_run_metadata(dag_run),
        )
    ]


def get_dag_run_metadata(dag_run: DagRun) -> Mapping[str, Any]:
    return {
        **get_common_metadata(dag_run),
        "Run Details": MarkdownMetadataValue(f"[View Run]({dag_run.url})"),
        "Start Date": TimestampMetadataValue(dag_run.start_date.timestamp()),
        "End Date": TimestampMetadataValue(dag_run.end_date.timestamp()),
        EFFECTIVE_TIMESTAMP_METADATA_KEY: TimestampMetadataValue(dag_run.end_date.timestamp()),
    }


def get_common_metadata(dag_run: DagRun) -> Mapping[str, Any]:
    return {
        "Airflow Run ID": dag_run.run_id,
        "Run Metadata (raw)": JsonMetadataValue(dag_run.metadata),
        "Run Type": dag_run.run_type,
        "Airflow Config": JsonMetadataValue(dag_run.config),
        "Creation Timestamp": TimestampMetadataValue(get_current_timestamp()),
    }


def get_task_instance_metadata(dag_run: DagRun, task_instance: TaskInstance) -> Mapping[str, Any]:
    return {
        **get_common_metadata(dag_run),
        "Run Details": MarkdownMetadataValue(f"[View Run]({task_instance.details_url})"),
        "Task Logs": MarkdownMetadataValue(f"[View Logs]({task_instance.log_url})"),
        "Start Date": TimestampMetadataValue(task_instance.start_date.timestamp()),
        "End Date": TimestampMetadataValue(task_instance.end_date.timestamp()),
        EFFECTIVE_TIMESTAMP_METADATA_KEY: TimestampMetadataValue(
            task_instance.end_date.timestamp()
        ),
    }


def materializations_for_task_instance(
    airflow_data: AirflowDefinitionsData,
    dag_run: DagRun,
    task_instance: TaskInstance,
) -> Sequence[AssetMaterialization]:
    mats = []
    asset_keys = airflow_data.asset_keys_in_task(dag_run.dag_id, task_instance.task_id)
    for asset_key in asset_keys:
        mats.append(
            AssetMaterialization(
                asset_key=asset_key,
                description=task_instance.note,
                metadata=get_task_instance_metadata(dag_run, task_instance),
            )
        )
    return mats
