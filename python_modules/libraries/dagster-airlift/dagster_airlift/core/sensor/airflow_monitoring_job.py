from collections.abc import Iterable, Iterator, Mapping, Sequence
from datetime import timedelta
from typing import Optional, Union

from dagster import (
    AssetCheckKey,
    AssetKey,
    AssetMaterialization,
    DefaultSensorStatus,
    RunRequest,
    SensorDefinition,
    SensorEvaluationContext,
    SensorResult,
    _check as check,
    sensor,
)
from dagster._annotations import beta
from dagster._core.definitions.asset_check_evaluation import AssetCheckEvaluation
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.decorators.job_decorator import job
from dagster._core.definitions.decorators.op_decorator import op
from dagster._core.definitions.decorators.schedule_decorator import schedule
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetObservation
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.repository_definition.repository_definition import (
    RepositoryDefinition,
)
from dagster._core.definitions.run_request import SkipReason
from dagster._core.definitions.schedule_definition import DefaultScheduleStatus, ScheduleEvaluationContext
from dagster._core.errors import (
    DagsterInvariantViolationError,
    DagsterUserCodeExecutionError,
    user_code_error_boundary,
)
from dagster._core.execution.context.op_execution_context import OpExecutionContext
from dagster._core.storage.dagster_run import DagsterRun, RunsFilter
from dagster._core.utils import make_new_run_id
from dagster._grpc.client import DEFAULT_SENSOR_GRPC_TIMEOUT
from dagster._record import record
from dagster._serdes import deserialize_value, serialize_value
from dagster._time import datetime_from_timestamp, get_current_datetime
from dagster_shared.serdes import whitelist_for_serdes

from dagster_airlift.constants import (
    AUTOMAPPED_TASK_METADATA_KEY,
    DAG_ID_TAG_KEY,
    DAG_RUN_ID_TAG_KEY,
    EFFECTIVE_TIMESTAMP_METADATA_KEY,
    TASK_ID_TAG_KEY,
)
from dagster_airlift.core.airflow_defs_data import AirflowDefinitionsData, MappedAsset
from dagster_airlift.core.airflow_instance import AirflowInstance
from dagster_airlift.core.runtime_representations import DagRun, TaskInstance
from dagster_airlift.core.sensor.event_translation import (
    AssetEvent,
    DagsterEventTransformerFn,
    default_event_transformer,
    get_timestamp_from_materialization,
    synthetic_mats_for_mapped_asset_keys,
    synthetic_mats_for_mapped_dag_asset_keys,
    synthetic_mats_for_peered_dag_asset_keys,
    synthetic_mats_for_task_instance,
)

MAIN_LOOP_TIMEOUT_SECONDS = DEFAULT_SENSOR_GRPC_TIMEOUT - 20
DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS = 30
START_LOOKBACK_SECONDS = 60  # Lookback one minute in time for the initial setting of the cursor.

# Indicates a newly started run.
@record
class NewlyStartedRun:
    idx: int
    dag_run: DagRun

# Indicates a new completed task instance.
@record
class CompletedTaskInstance:
    idx: int
    task_instance: TaskInstance
    dag_run: DagRun

# Indicates a newly completed run.
@record
class CompletedRun:
    idx: int  

AirflowEvent = Union[NewlyStartedRun, CompletedTaskInstance, CompletedRun]

@whitelist_for_serdes
class AirflowEventType(Enum):
    """The type of event emitted by the Airflow sensor."""

    NEWLY_STARTED_RUN = "NEWLY_STARTED_RUN"
    COMPLETED_TASK_INSTANCE = "COMPLETED_TASK_INSTANCE"
    COMPLETED_RUN = "COMPLETED_RUN"

@whitelist_for_serdes
@record
class IterPauseInfo:
    """Information about the pause in the iteration."""
    # What event type we were processing when the pause began.
    af_event_type: AirflowEventType
    # The index of the paused event.
    idx: int

@whitelist_for_serdes
@record
class AirflowPollingSensorCursor:
    """A cursor that stores the last effective timestamp and the last polled dag id."""

    started_run_ids: set[str] = set()
    # The time range we are looking for events in.
    time_range_start: float
    time_range_end: float
    iter_pause_info: Optional[AirflowEvent] = None



class AirliftSensorEventTransformerError(DagsterUserCodeExecutionError):
    """Error raised when an error occurs in the event transformer function."""


@beta
def build_airflow_monitoring_job(
    *,
    mapped_assets: Sequence[MappedAsset],
    airflow_instance: AirflowInstance,
) -> Definitions:
    """The constructed job polls the Airflow instance for activity, and inserts asset events into Dagster's event log.
    """
    airflow_data = AirflowDefinitionsData(
        airflow_instance=airflow_instance, airflow_mapped_assets=mapped_assets
    )

    @op(
        name=f"{airflow_data.airflow_instance.name}__airflow_dag_status_sensor",
    )
    def monitor_dags(context: OpExecutionContext) -> None:
        """The main function that runs the sensor. It polls the Airflow instance for activity and emits asset events."""
        # get previously processed time range from run tags
        current_date = get_current_datetime()
        prev_run = next(iter(context.instance.get_runs(
            filters=RunsFilter(job_name=context.job_name),
            limit=1,
        )), None)
        if prev_run:
            # Start from the end of the last run
            range_start = float(prev_run.tags["dagster-airlift/monitoring_job_range_end"])
        else:
            range_start = current_date.timestamp() - START_LOOKBACK_SECONDS
        range_end = current_date.timestamp()
        context.instance.add_run_tags(run_id=context.run_id, new_tags={"dagster-airlift/monitoring_job_range_start": str(range_start), "dagster-airlift/monitoring_job_range_end": str(range_end)})
        context.log.info(
            f"Airflow Monitoring Job: Processing from {datetime_from_timestamp(range_start)} to {datetime_from_timestamp(range_end)}"
        )
        # Gotta actually build out the mapping layer
        dag_ids = set()

        offset = 0
        # First, process newly started runs.
        while True:
            (newly_started_runs, total_entries) = airflow_instance.get_dag_runs_batch(
                states=["running", "queued"],
                # This will probably require a new property
                dag_ids=list(dag_ids),
                start_date_gte=datetime_from_timestamp(range_start),
                start_date_lte=datetime_from_timestamp(range_end),
                offset=offset,
            )
            for run in newly_started_runs:
                run_id = make_new_run_id()
                context.instance.create_run_for_job(
                    run_id=run_id,
                    job_def=...,
                    tags={
                        DAG_RUN_ID_TAG_KEY: run.run_id,
                        DAG_ID_TAG_KEY: run.dag_id,
                    },
                    # Need to map dag status to run status.
                    status=...,
                )
                # Emit asset planned materializations for the run.
                for asset in []:
                    pass
            offset += len(newly_started_runs)
            if offset >= total_entries:
                break
        # Then, process completed successful task instances.
        task_instances = airflow_instance.get_task_instance_batch_time_range(
            states=["success"],
            dag_ids=list(dag_ids),
            end_date_gte=datetime_from_timestamp(range_start),
            end_date_lte=datetime_from_timestamp(range_end),
        )

        for task_instance in task_instances:
            pass

        
        yield from [
            NewlyStartedRun(
                idx=i+offset+1,
                dag_run=dag_run,
            )
            for i, dag_run in enumerate(newly_started_runs)
        ]
        offset += len(newly_started_runs)
        if offset >= total_entries:
            break


    @job(name=f"{airflow_data.airflow_instance.name}__airflow_monitoring_job") 
    def airflow_monitoring_job():
        monitor_dags()
    
    @schedule(
        job=airflow_monitoring_job,
        cron_schedule="* * * * *",
        name=f"{airflow_data.airflow_instance.name}__airflow_monitoring_job_schedule",
        default_status=DefaultScheduleStatus.RUNNING,
    )
    def airflow_monitoring_job_schedule(context: ScheduleEvaluationContext) -> Union[RunRequest, SkipReason]:
        """The schedule that runs the sensor job."""
        # Get the last run for this job
        last_run = next(iter(context.instance.get_runs(
            filters=RunsFilter(job_name=airflow_monitoring_job.name),
            limit=1,
        )), None)
        if not last_run or last_run.is_finished:
            return RunRequest()
        else:
            return SkipReason("Monitoring job is already running.")


def sorted_asset_events(
    asset_events: Sequence[AssetEvent],
    repository_def: RepositoryDefinition,
) -> list[AssetEvent]:
    """Sort materializations by end date and toposort order."""
    topo_aks = repository_def.asset_graph.toposorted_asset_keys
    materializations_and_timestamps = [
        (get_timestamp_from_materialization(mat), mat) for mat in asset_events
    ]
    return [
        sorted_event[1]
        for sorted_event in sorted(
            materializations_and_timestamps, key=lambda x: (x[0], topo_aks.index(x[1].asset_key))
        )
    ]


def _get_transformer_result(
    event_transformer_fn: Optional[DagsterEventTransformerFn],
    context: SensorEvaluationContext,
    airflow_data: AirflowDefinitionsData,
    all_asset_events: Sequence[AssetMaterialization],
) -> Sequence[AssetEvent]:
    if not event_transformer_fn:
        return all_asset_events

    with user_code_error_boundary(
        AirliftSensorEventTransformerError,
        lambda: f"Error occurred during event transformation for {airflow_data.airflow_instance.name}",
    ):
        updated_asset_events = list(event_transformer_fn(context, airflow_data, all_asset_events))

    for asset_event in updated_asset_events:
        if not isinstance(
            asset_event, (AssetMaterialization, AssetObservation, AssetCheckEvaluation)
        ):
            raise DagsterInvariantViolationError(
                f"Event transformer function must return AssetMaterialization, AssetObservation, or AssetCheckEvaluation objects. Got {type(asset_event)}."
            )
        if EFFECTIVE_TIMESTAMP_METADATA_KEY not in asset_event.metadata:
            raise DagsterInvariantViolationError(
                f"All returned events must have an effective timestamp, but {asset_event} does not. An effective timestamp can be used by setting dagster_airlift.constants.EFFECTIVE_TIMESTAMP_METADATA_KEY with a dagster.TimestampMetadataValue."
            )
    return updated_asset_events


@record
class BatchResult:
    # The index into the retrieved set of runs. This is used to set the cursor for the next sensor tick.
    idx_started_runs: int
    # New asset materialization events that we've seen.
    asset_mats: Sequence[AssetMaterialization]
    # Dag runs in a started state.
    started_dag_runs: Mapping[str, DagRun]
    all_asset_keys_materialized: set[AssetKey]
    # The index into the retrieved set of completed runs. This is used to set the cursor for the next sensor tick.
    idx_completed_runs: int = 0

def processed_airflow_event_stream(
    context: SensorEvaluationContext,
    cursor: AirflowPollingSensorCursor,
    airflow_instance: AirflowInstance,
    airflow_defs_data: AirflowDefinitionsData,
) -> Iterator[AirflowEvent]:
    # Events only emitted upon being fully "processed" and can be used in cursoring.
    pass
def raw_airflow_event_stream(
    context: SensorEvaluationContext,
    cursor: AirflowPollingSensorCursor,
    airflow_instance: AirflowInstance,
    dag_ids: set[str],
) -> Iterator[AirflowEvent]:
    pass

def started_run_stream(
    context: SensorEvaluationContext,
    cursor: AirflowPollingSensorCursor,
    airflow_instance: AirflowInstance,
    dag_ids: set[str],
) -> Iterator["NewlyStartedRun"]:
    """Create a stream of newly started runs."""
    # Get the new started runs from the Airflow instance.
    offset = cursor.started_run_query_offset or 0
    while True:
        (newly_started_runs, total_entries) = airflow_instance.get_dag_runs_batch(
            states=["running", "queued"],
            # This will probably require a new property
            dag_ids=list(dag_ids),
            start_date_gte=datetime_from_timestamp(cursor.start_date_gte) if cursor.start_date_gte else None,
            start_date_lte=datetime_from_timestamp(cursor.start_date_lte) if cursor.start_date_lte else None,
            offset=offset,
        )
        yield from [
            NewlyStartedRun(
                idx=i+offset+1,
                dag_run=dag_run,
            )
            for i, dag_run in enumerate(newly_started_runs)
        ]
        offset += len(newly_started_runs)
        if offset >= total_entries:
            break

def completed_task_instance_stream(
    context: SensorEvaluationContext,
    cursor: AirflowPollingSensorCursor,
    airflow_instance: AirflowInstance,
    dag_ids: set[str],
) -> Iterator["CompletedTaskInstance"]:
    """Create a stream of completed task instances."""
    # Get the new completed task instances from the Airflow instance.
    offset = cursor.started_run_query_offset or 0
    while True:
        (completed_task_instances, total_entries) = airflow_instance.get_task_instance_batch_time_range(
            states=["success"],
            dag_ids=list(dag_ids),
            end_date_gte=datetime_from_timestamp(cursor.start_date_gte),
            end_date_lte=datetime_from_timestamp(cursor.start_date_lte),
        )
        yield from [
            CompletedTaskInstance(
                idx=i+offset+1,
                task_instance=task_instance,
                dag_run=task_instance.dag_run,
            )
            for i, task_instance in enumerate(completed_task_instances)
        ]
        offset += len(completed_task_instances)
        if offset >= total_entries:
            break




BatchResult = Union[NewlyStartedRun, ProcessedTaskInstance, ProcessedCompletedRun] 

def build_synthetic_asset_materializations(
    context: SensorEvaluationContext,
    airflow_instance: AirflowInstance,
    dag_run: DagRun,
    airflow_data: AirflowDefinitionsData,
) -> list[AssetMaterialization]:
    """In this function we need to return the asset materializations we want to synthesize
    on behalf of the user.

    This happens when the user has modeled an external asset that has a corresponding
    task in airflow which is not proxied to Dagster. We want to detect the case
    where there is a successful airflow task instance that is mapped to a
    dagster asset but is _not_ proxied, and then synthensize a materialization
    for observability.

    We do this by querying for successful task instances in Airflow. And then
    for each successful task we see it there exists a Dagster Run tagged with
    the run id. If there is not Dagster run, we know the task was not proxied.

    Task instances are mutable in Airflow, so we are not guaranteed to register
    every task instance. If, for example, the sensor is paused, and then there are
    multiple task clearings, we will only register the last materialization.

    This also currently does not support dynamic tasks in Airflow, in which case
    the use should instead map at the dag-level granularity.
    """
    # https://linear.app/dagster-labs/issue/FOU-444/make-sensor-work-with-an-airflow-dag-run-that-has-more-than-1000
    dagster_runs = context.instance.get_runs(
        filters=RunsFilter(tags={DAG_RUN_ID_TAG_KEY: dag_run.run_id}),
        limit=1000,
    )
    context.log.info(f"Found {len(dagster_runs)} dagster runs for {dag_run.run_id}")

    context.log.info(
        f"Airlift Sensor: Found dagster run ids: {[run.run_id for run in dagster_runs]}"
        f" for airflow run id {dag_run.run_id} and dag id {dag_run.dag_id}"
    )
    synthetic_mats = []
    # Peered dag-level materializations will always be emitted.
    synthetic_mats.extend(synthetic_mats_for_peered_dag_asset_keys(dag_run, airflow_data))
    # If there is a dagster run for this dag, we don't need to synthesize materializations for mapped dag assets.
    if not dagster_runs:
        synthetic_mats.extend(synthetic_mats_for_mapped_dag_asset_keys(dag_run, airflow_data))
    synthetic_mats.extend(
        get_synthetic_task_mats(
            airflow_instance=airflow_instance,
            dagster_runs=dagster_runs,
            dag_run=dag_run,
            airflow_data=airflow_data,
            context=context,
        )
    )
    return synthetic_mats


def get_synthetic_task_mats(
    airflow_instance: AirflowInstance,
    dagster_runs: Sequence[DagsterRun],
    dag_run: DagRun,
    airflow_data: AirflowDefinitionsData,
    context: SensorEvaluationContext,
) -> list[AssetMaterialization]:
    task_instances = airflow_instance.get_task_instance_batch(
        run_id=dag_run.run_id,
        dag_id=dag_run.dag_id,
        task_ids=[task_id for task_id in airflow_data.task_ids_in_dag(dag_run.dag_id)],
        states=["success"],
    )
    check.invariant(
        len({ti.task_id for ti in task_instances}) == len(task_instances),
        "Assuming one task instance per task_id for now. Dynamic Airflow tasks not supported.",
    )
    synthetic_mats = []
    context.log.info(f"Found {len(task_instances)} task instances for {dag_run.run_id}")
    context.log.info(f"All task instances {task_instances}")
    dagster_runs_by_task_id = {
        run.tags[TASK_ID_TAG_KEY]: run for run in dagster_runs if TASK_ID_TAG_KEY in run.tags
    }
    task_instances_by_task_id = {ti.task_id: ti for ti in task_instances}
    for task_id, task_instance in task_instances_by_task_id.items():
        # No dagster runs means that the computation that materializes the asset was not proxied to Dagster.
        # Therefore the dags ran completely in Airflow, and we will synthesize materializations in Dagster corresponding to that data run.
        if task_id not in dagster_runs_by_task_id:
            context.log.info(
                f"Synthesizing materialization for tasks {task_id} in dag {dag_run.dag_id} because no dagster run found."
            )
            synthetic_mats.extend(
                synthetic_mats_for_task_instance(airflow_data, dag_run, task_instance)
            )
        else:
            # We *always* emit for the automapped tasks, even if they are proxied
            asset_keys_to_emit = automapped_tasks_asset_keys(dag_run, airflow_data, task_instance)

            synthetic_mats.extend(
                synthetic_mats_for_mapped_asset_keys(
                    dag_run=dag_run, task_instance=task_instance, asset_keys=asset_keys_to_emit
                )
            )

            context.log.info(
                f"Dagster run found for task {task_id} in dag {dag_run.dag_id}. Run {dagster_runs_by_task_id[task_id].run_id}"
            )
    return synthetic_mats


def automapped_tasks_asset_keys(
    dag_run: DagRun, airflow_data: AirflowDefinitionsData, task_instance: TaskInstance
) -> set[AssetKey]:
    asset_keys_to_emit = set()
    asset_keys = airflow_data.asset_keys_in_task(dag_run.dag_id, task_instance.task_id)
    for asset_key in asset_keys:
        spec = airflow_data.all_asset_specs_by_key[asset_key]
        if spec.metadata.get(AUTOMAPPED_TASK_METADATA_KEY):
            asset_keys_to_emit.add(asset_key)
    return asset_keys_to_emit
