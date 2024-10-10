from typing import AbstractSet, Any, Callable, Iterable, Mapping, Sequence, Union, cast

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
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.definitions.time_window_partitions import TimeWindowPartitionsDefinition
from dagster._time import datetime_from_timestamp, get_current_timestamp

from dagster_airlift.constants import (
    AIRFLOW_RUN_ID_METADATA_KEY,
    AIRFLOW_TASK_INSTANCE_LOGICAL_DATE_METADATA_KEY,
    EFFECTIVE_TIMESTAMP_METADATA_KEY,
)
from dagster_airlift.core.airflow_defs_data import AirflowDefinitionsData
from dagster_airlift.core.airflow_instance import DagRun, TaskInstance

AssetEvent = Union[AssetMaterialization, AssetObservation, AssetCheckEvaluation]
DagsterEventTransformerFn = Callable[
    [SensorEvaluationContext, AirflowDefinitionsData, Sequence[AssetMaterialization]],
    Iterable[AssetEvent],
]


def default_event_transformer(
    context: SensorEvaluationContext,
    airflow_data: AirflowDefinitionsData,
    materializations: Sequence[AssetMaterialization],
) -> Iterable[AssetEvent]:
    """The default event transformer function, which attaches a partition key to materializations which are from time-window partitioned assets."""
    for mat in materializations:
        asset_spec = airflow_data.get_asset_spec_for_key(mat.asset_key)
        if not asset_spec.is_time_window_partitioned:
            yield mat
            continue
        airflow_logical_date_timestamp: float = cast(
            TimestampMetadataValue, mat.metadata[AIRFLOW_TASK_INSTANCE_LOGICAL_DATE_METADATA_KEY]
        ).value
        airflow_run_id = cast(str, mat.metadata[AIRFLOW_RUN_ID_METADATA_KEY])
        partition = get_partition_key_from_existing_materialization(
            partitions_def=cast(TimeWindowPartitionsDefinition, asset_spec.partitions_def),
            airflow_logical_date_timestamp=airflow_logical_date_timestamp,
            airflow_run_id=airflow_run_id,
            asset_key=mat.asset_key,
        )
        partitioned_mat = mat._replace(partition=partition)
        yield partitioned_mat


def get_partition_key_from_existing_materialization(
    partitions_def: PartitionsDefinition,
    airflow_logical_date_timestamp: float,
    airflow_run_id: str,
    asset_key: AssetKey,
) -> str:
    partitions_def = check.inst(
        partitions_def,
        TimeWindowPartitionsDefinition,
        "Only time window-partitioned assets are supported.",
    )
    airflow_logical_date_in_tz = datetime_from_timestamp(
        airflow_logical_date_timestamp, partitions_def.timezone
    )

    # Assuming that "logical_date" lies on a partition, the previous partition window
    # (where upper bound can be the passed-in date, which is why we set respect_bounds=False)
    # will end on the logical date. This would indicate that there is a partition for the logical date.
    partition_window = check.not_none(
        partitions_def.get_prev_partition_window(airflow_logical_date_in_tz, respect_bounds=False),
        f"Could not find partition for airflow logical date {airflow_logical_date_in_tz.isoformat()}. This likely means that your partition range is too small to cover the logical date.",
    )
    check.invariant(
        airflow_logical_date_in_tz.timestamp() == partition_window.end.timestamp(),
        (
            "Expected logical date to match a partition in the partitions definition. This likely means that "
            "The partition range is not aligned with the scheduling interval in airflow."
        ),
    )
    check.invariant(
        airflow_logical_date_in_tz.timestamp() >= partitions_def.start.timestamp(),
        (
            f"For Airflow run {airflow_run_id} "
            f"logical date is before the start of the partitions definition in asset key {asset_key.to_user_string()}. "
            "Ensure that the start date of your PartitionsDefinition is early enough to capture current runs coming from airflow."
        ),
    )
    return partitions_def.get_partition_key_for_timestamp(airflow_logical_date_timestamp)


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
        AIRFLOW_RUN_ID_METADATA_KEY: dag_run.run_id,
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
        AIRFLOW_TASK_INSTANCE_LOGICAL_DATE_METADATA_KEY: TimestampMetadataValue(
            task_instance.logical_date.timestamp()
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
