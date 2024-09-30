from typing import Any, Callable, Iterable, List, Mapping, Sequence

from dagster import (
    AssetKey,
    AssetMaterialization,
    JsonMetadataValue,
    MarkdownMetadataValue,
    PartitionsDefinition,
    TimestampMetadataValue,
    TimeWindowPartitionsDefinition,
    _check as check,
)
from dagster._time import get_current_timestamp, get_timezone

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
        spec = airflow_data.resolved_airflow_defs.get_asset_graph().get_asset_spec(asset_key)
        partition = (
            get_partition_key_from_task_instance(spec.partitions_def, task_instance, asset_key)
            if spec.partitions_def
            else None
        )
        mats.append(
            AssetMaterialization(
                asset_key=asset_key,
                description=task_instance.note,
                metadata=get_task_instance_metadata(dag_run, task_instance),
                partition=partition,
            )
        )
    return mats


def get_partition_key_from_task_instance(
    partitions_def: PartitionsDefinition, task_instance: TaskInstance, asset_key: AssetKey
) -> str:
    partitions_def = check.inst(
        partitions_def,
        TimeWindowPartitionsDefinition,
        "Only time window-partitioned assets are supported.",
    )
    airflow_logical_date = task_instance.logical_date
    airflow_logical_date_timezone = airflow_logical_date.tzinfo
    partitions_def_timezone = get_timezone(partitions_def.timezone)
    check.invariant(
        airflow_logical_date_timezone == partitions_def_timezone,
        (
            f"The timezone of the retrieved logical date from the airflow run ({airflow_logical_date_timezone}) does not "
            f"match that of the partitions definition ({partitions_def_timezone}) for asset key {asset_key.to_user_string()}."
            "To ensure consistent behavior, the timezone of the logical date must match the timezone of the partitions definition."
        ),
    )
    # Assuming that "logical_date" lies on a partition, the previous partition window
    # (where upper bound can be the passed-in date, which is why we set respect_bounds=False)
    # will end on the logical date. This would indicate that there is a partition for the logical date.
    partition_window = check.not_none(
        partitions_def.get_prev_partition_window(airflow_logical_date, respect_bounds=False),
        f"Could not find partition for airflow logical date {airflow_logical_date.isoformat()}. This likely means that your partition range is too small to cover the logical date.",
    )
    check.invariant(
        airflow_logical_date.timestamp() == partition_window.end.timestamp(),
        (
            "Expected logical date to match a partition in the partitions definition. This likely means that "
            "The partition range is not aligned with the scheduling interval in airflow."
        ),
    )
    check.invariant(
        airflow_logical_date.timestamp() >= partitions_def.start.timestamp(),
        (
            f"For run {task_instance.run_id} in dag {task_instance.dag_id}, "
            f"Logical date is before the start of the partitions definition in asset key {asset_key.to_user_string()}. "
            "Ensure that the start date of your PartitionsDefinition is early enough to capture current runs coming from airflow."
        ),
    )
    return partitions_def.get_partition_key_for_timestamp(airflow_logical_date.timestamp())
