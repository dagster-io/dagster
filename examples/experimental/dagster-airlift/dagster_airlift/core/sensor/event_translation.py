from typing import AbstractSet, Any, Callable, Iterable, Mapping, Sequence, Union

from dagster import (
    AssetMaterialization,
    AssetObservation,
    JsonMetadataValue,
    MarkdownMetadataValue,
    SensorEvaluationContext,
    TimestampMetadataValue,
    _check as check,
)
from dagster._core.definitions.asset_check_evaluation import AssetCheckEvaluation
from dagster._core.definitions.asset_key import AssetKey
from dagster._time import get_current_timestamp

from dagster_airlift.constants import EFFECTIVE_TIMESTAMP_METADATA_KEY
from dagster_airlift.core.airflow_defs_data import AirflowDefinitionsData
from dagster_airlift.core.airflow_instance import DagRun, TaskInstance

AssetEvent = Union[AssetMaterialization, AssetObservation, AssetCheckEvaluation]
DagsterEventTransformerFn = Callable[
    [SensorEvaluationContext, AirflowDefinitionsData, Sequence[AssetMaterialization]],
    Iterable[AssetEvent],
]


def get_timestamp_from_materialization(event: AssetEvent) -> float:
    return check.float_param(
        event.metadata[EFFECTIVE_TIMESTAMP_METADATA_KEY].value,
        "Materialization Effective Timestamp",
    )


def materializations_for_dag_run(
    dag_run: DagRun, airflow_data: AirflowDefinitionsData
) -> Sequence[AssetMaterialization]:
    return [
        AssetMaterialization(
            asset_key=asset_key, description=dag_run.note, metadata=get_dag_run_metadata(dag_run)
        )
        for asset_key in airflow_data.asset_keys_per_dag[dag_run.dag_id]
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


def synthetic_mats_for_task_instance(
    airflow_data: AirflowDefinitionsData,
    dag_run: DagRun,
    task_instance: TaskInstance,
) -> Sequence[AssetMaterialization]:
    asset_keys = airflow_data.asset_keys_in_task(dag_run.dag_id, task_instance.task_id)
    return synthetic_mats_for_mapped_asset_keys(dag_run, task_instance, asset_keys)


def synthetic_mats_for_mapped_asset_keys(
    dag_run: DagRun, task_instance: TaskInstance, asset_keys: AbstractSet[AssetKey]
) -> Sequence[AssetMaterialization]:
    mats = []
    for asset_key in asset_keys:
        mats.append(
            AssetMaterialization(
                asset_key=asset_key,
                description=task_instance.note,
                metadata=get_task_instance_metadata(dag_run, task_instance),
            )
        )
    return mats
