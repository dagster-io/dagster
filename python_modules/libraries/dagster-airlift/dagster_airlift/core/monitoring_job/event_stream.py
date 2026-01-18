import asyncio
from abc import ABC, abstractmethod
from collections.abc import Iterator
from itertools import chain
from typing import Optional, Union

from dagster import (
    AssetMaterialization,
    _check as check,
)
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.metadata.metadata_value import MetadataValue
from dagster._core.events import (
    AssetMaterializationPlannedData,
    DagsterEvent,
    DagsterEventType,
    JobFailureData,
    StepMaterializationData,
)
from dagster._core.execution.context.op_execution_context import OpExecutionContext
from dagster._core.remote_origin import RemoteJobOrigin
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus
from dagster._core.storage.tags import EXTERNAL_JOB_SOURCE_TAG_KEY
from dagster._core.utils import make_new_run_id
from dagster._record import record
from dagster._time import datetime_from_timestamp
from dagster._utils.merger import merge_dicts

from dagster_airlift.constants import (
    DAG_ID_TAG_KEY,
    DAG_RUN_ID_TAG_KEY,
    DAG_RUN_URL_TAG_KEY,
    NO_STEP_KEY,
    OBSERVATION_RUN_TAG_KEY,
)
from dagster_airlift.core.airflow_defs_data import AirflowDefinitionsData
from dagster_airlift.core.airflow_instance import AirflowInstance
from dagster_airlift.core.monitoring_job.utils import (
    extract_metadata_from_logs,
    get_dagster_run_for_airflow_repr,
    get_externally_managed_runs_from_handle,
    structured_log,
)
from dagster_airlift.core.runtime_representations import DagRun, TaskInstance


class AirflowEvent(ABC):
    @property
    @abstractmethod
    def timestamp(self) -> float:
        pass

    @abstractmethod
    def persist_state(
        self,
        context: OpExecutionContext,
        airflow_data: AirflowDefinitionsData,
        airflow_instance: AirflowInstance,
    ) -> None:
        """Persist the state of the event to Dagster."""
        pass


@record
class DagRunStarted(AirflowEvent):
    dag_run: DagRun

    @property
    def timestamp(self) -> float:
        return self.dag_run.start_date.timestamp()

    def persist_state(
        self,
        context: OpExecutionContext,
        airflow_data: AirflowDefinitionsData,
        airflow_instance: AirflowInstance,
    ) -> None:
        # If the run is already in Dagster, we don't need to do anything.
        relevant_job_def = airflow_data.airflow_mapped_jobs_by_dag_handle.get(
            self.dag_run.dag_handle
        )
        # Only if we have a relevant job def do we need to mess with creating runs.
        if not relevant_job_def:
            return
        dagster_run_id = make_new_run_id()
        context.instance.run_storage.add_historical_run(
            dagster_run=DagsterRun(
                run_id=dagster_run_id,
                job_name=relevant_job_def.name,
                tags={
                    DAG_RUN_ID_TAG_KEY: self.dag_run.run_id,
                    DAG_ID_TAG_KEY: self.dag_run.dag_id,
                    EXTERNAL_JOB_SOURCE_TAG_KEY: "airflow",
                    DAG_RUN_URL_TAG_KEY: self.dag_run.url,
                    OBSERVATION_RUN_TAG_KEY: "true",
                },
                status=DagsterRunStatus.NOT_STARTED,
                remote_job_origin=RemoteJobOrigin(
                    # We steal the repository origin from the original run.
                    # This allows the UI to link the run we're creating here back to the
                    # job in Dagster.
                    # It's not set in test contexts
                    repository_origin=context.run.remote_job_origin.repository_origin,
                    job_name=relevant_job_def.name,
                )
                if context.run.remote_job_origin
                else None,
            ),
            run_creation_time=self.dag_run.start_date,
        )

        context.instance.report_dagster_event(
            run_id=dagster_run_id,
            dagster_event=DagsterEvent(
                event_type_value="PIPELINE_START",
                job_name=relevant_job_def.name,
            ),
            timestamp=self.dag_run.start_date.timestamp(),
        )

        planned_asset_keys = {
            *airflow_data.all_asset_keys_by_dag_handle[self.dag_run.dag_handle],
            *{
                asset_key
                for task_handle, keys in airflow_data.mapped_asset_keys_by_task_handle.items()
                for asset_key in keys
                if task_handle.dag_id == self.dag_run.dag_id
            },
        }
        for asset_key in planned_asset_keys:
            context.instance.report_dagster_event(
                run_id=dagster_run_id,
                dagster_event=DagsterEvent.build_asset_materialization_planned_event(
                    job_name=relevant_job_def.name,
                    asset_materialization_planned_data=AssetMaterializationPlannedData(
                        asset_key=asset_key,
                    ),
                    step_key=NO_STEP_KEY,
                ),
                timestamp=self.dag_run.start_date.timestamp(),
            )


@record
class TaskInstanceCompleted(AirflowEvent):
    task_instance: TaskInstance
    metadata: dict[str, MetadataValue]

    @property
    def timestamp(self) -> float:
        return self.task_instance.end_date.timestamp()

    def persist_state(
        self,
        context: OpExecutionContext,
        airflow_data: AirflowDefinitionsData,
        airflow_instance: AirflowInstance,
    ) -> None:
        corresponding_run = get_dagster_run_for_airflow_repr(context, self.task_instance)
        externally_managed_runs = get_externally_managed_runs_from_handle(
            context, self.task_instance.task_handle, self.task_instance.run_id
        )

        per_key_metadata = (
            merge_dicts(
                *(_per_asset_metadata_from_run(context, run) for run in externally_managed_runs)
            )
            if externally_managed_runs
            else {}
        )

        for asset in airflow_data.mapped_asset_keys_by_task_handle[self.task_instance.task_handle]:
            # IMPROVEME: Add metadata to the materialization event.
            _report_materialization(
                context=context,
                corresponding_run=corresponding_run,
                materialization=AssetMaterialization(
                    asset_key=asset,
                    metadata=merge_dicts(per_key_metadata.get(asset, {}), self.metadata),
                ),
                airflow_event=self.task_instance,
            )


@record
class DagRunCompleted(AirflowEvent):
    dag_run: DagRun

    @property
    def timestamp(self) -> float:
        return self.dag_run.end_date.timestamp()

    def persist_state(
        self,
        context: OpExecutionContext,
        airflow_data: AirflowDefinitionsData,
        airflow_instance: AirflowInstance,
    ) -> None:
        corresponding_run = get_dagster_run_for_airflow_repr(context, self.dag_run)
        for asset in airflow_data.all_asset_keys_by_dag_handle[self.dag_run.dag_handle]:
            _report_materialization(
                context=context,
                corresponding_run=corresponding_run,
                materialization=AssetMaterialization(asset_key=asset),
                airflow_event=self.dag_run,
            )

        if not corresponding_run:
            context.log.warning(
                f"Airflow Monitoring Job: No corresponding Dagster run found for completed Airflow run {self.dag_run.run_id}. Skipping run event emission."
            )
            return
        dagster_run_id = corresponding_run.run_id
        if self.dag_run.state == "success":
            structured_log(
                context,
                f"Emitting pipeline success event for run {dagster_run_id}.",
            )
            event = DagsterEvent(
                event_type_value="PIPELINE_SUCCESS",
                job_name=corresponding_run.job_name,
            )
        else:
            structured_log(
                context,
                f"Emitting pipeline failure event for run {dagster_run_id}.",
            )
            event = DagsterEvent(
                event_type_value="PIPELINE_FAILURE",
                job_name=corresponding_run.job_name,
                event_specific_data=JobFailureData(
                    error=None, failure_reason=None, first_step_failure_event=None
                ),
            )
        context.instance.report_dagster_event(
            run_id=dagster_run_id, dagster_event=event, timestamp=self.dag_run.end_date.timestamp()
        )


def _process_started_runs(
    context: OpExecutionContext,
    airflow_data: AirflowDefinitionsData,
    airflow_instance: AirflowInstance,
    range_start: float,
    range_end: float,
) -> Iterator[DagRunStarted]:
    offset = 0
    while True:
        (newly_started_runs, total_entries) = airflow_instance.get_dag_runs_batch(
            states=["running", "queued"],
            # When monitoring started runs; we only need to monitor dags that have an associated job.
            dag_ids=[
                dag_handle.dag_id
                for dag_handle in airflow_data.airflow_mapped_jobs_by_dag_handle.keys()
            ],
            start_date_gte=datetime_from_timestamp(range_start),
            start_date_lte=datetime_from_timestamp(range_end),
            offset=offset,
        )
        structured_log(
            context,
            f"Found {len(newly_started_runs)} newly started runs in the time range {datetime_from_timestamp(range_start)} to {datetime_from_timestamp(range_end)}",
        )
        yield from (DagRunStarted(dag_run=dag_run) for dag_run in newly_started_runs)
        offset += len(newly_started_runs)
        if offset >= total_entries:
            break


def _process_completed_runs(
    context: OpExecutionContext,
    airflow_data: AirflowDefinitionsData,
    airflow_instance: AirflowInstance,
    range_start: float,
    range_end: float,
) -> Iterator[Union[DagRunStarted, DagRunCompleted]]:
    offset = 0
    dag_ids_to_query = airflow_data.dag_ids_with_mapped_asset_keys | {
        handle.dag_id for handle in airflow_data.airflow_mapped_jobs_by_dag_handle.keys()
    }
    while True:
        (newly_completed_runs, total_entries) = airflow_instance.get_dag_runs_batch(
            states=["success", "failed", "up_for_retry"],
            dag_ids=list(dag_ids_to_query),
            end_date_gte=datetime_from_timestamp(range_start),
            end_date_lte=datetime_from_timestamp(range_end),
            offset=offset,
        )
        structured_log(
            context,
            f"Found {len(newly_completed_runs)} newly completed runs in the time range {datetime_from_timestamp(range_start)} to {datetime_from_timestamp(range_end)}",
        )
        for run in newly_completed_runs:
            corresponding_dagster_run = get_dagster_run_for_airflow_repr(context, run)
            if not corresponding_dagster_run:
                yield DagRunStarted(dag_run=run)
            yield DagRunCompleted(dag_run=run)
        offset += len(newly_completed_runs)
        if offset >= total_entries:
            break


async def _retrieve_logs_for_task_instance(
    context: OpExecutionContext,
    airflow_instance: AirflowInstance,
    task_instance: TaskInstance,
) -> TaskInstanceCompleted:
    logs = await asyncio.to_thread(
        airflow_instance.get_task_instance_logs,
        task_instance.dag_id,
        task_instance.task_id,
        task_instance.run_id,
        task_instance.try_number,
    )
    try:
        metadata = extract_metadata_from_logs(context, logs)
    except Exception as e:
        context.log.warning(
            f"An unexpected error occurred while extracting metadata from logs: {e}. Skipping metadata extraction for task instance {task_instance.task_id}."
        )
        metadata = {}

    return TaskInstanceCompleted(task_instance=task_instance, metadata=metadata)


async def _async_process_task_instances(
    context: OpExecutionContext,
    airflow_instance: AirflowInstance,
    task_instances: list[TaskInstance],
) -> list[TaskInstanceCompleted]:
    results = await asyncio.gather(
        *(
            _retrieve_logs_for_task_instance(context, airflow_instance, task_instance)
            for task_instance in task_instances
        )
    )

    return results


def _process_task_instances(
    context: OpExecutionContext,
    airflow_data: AirflowDefinitionsData,
    airflow_instance: AirflowInstance,
    range_start: float,
    range_end: float,
) -> Iterator[TaskInstanceCompleted]:
    # You'll notice that the query pattern here is different from the dag run query pattern.
    # That's because early Airflow 2 versions don't support batch size queries for task instances.
    # NOTE: In the case where we have a run which completed between iterations, we'll be emitting events for the run _after_ we've marked the run as finished.
    # so the timeline will be a bit screwed up.
    task_instances = airflow_instance.get_task_instance_batch_time_range(
        states=["success"],
        dag_ids=list(airflow_data.dag_ids_with_mapped_asset_keys),
        end_date_gte=datetime_from_timestamp(range_start),
        end_date_lte=datetime_from_timestamp(range_end),
    )
    structured_log(
        context,
        f"Found {len(task_instances)} completed task instances in the time range {datetime_from_timestamp(range_start)} to {datetime_from_timestamp(range_end)}",
    )
    yield from asyncio.run(_async_process_task_instances(context, airflow_instance, task_instances))


def persist_events(
    context: OpExecutionContext,
    airflow_data: AirflowDefinitionsData,
    airflow_instance: AirflowInstance,
    range_start: float,
    range_end: float,
) -> None:
    for event in sorted(
        chain(
            _process_started_runs(context, airflow_data, airflow_instance, range_start, range_end),
            _process_completed_runs(
                context, airflow_data, airflow_instance, range_start, range_end
            ),
            _process_task_instances(
                context, airflow_data, airflow_instance, range_start, range_end
            ),
        ),
        key=lambda event: event.timestamp,
    ):
        event.persist_state(context, airflow_data, airflow_instance)


def _report_materialization(
    *,
    context: OpExecutionContext,
    corresponding_run: Optional[DagsterRun],
    materialization: AssetMaterialization,
    airflow_event: Union[TaskInstance, DagRun],
) -> None:
    if corresponding_run:
        context.instance.report_dagster_event(
            run_id=corresponding_run.run_id,
            dagster_event=DagsterEvent(
                event_type_value="ASSET_MATERIALIZATION",
                job_name=corresponding_run.job_name,
                event_specific_data=StepMaterializationData(materialization=materialization),
            ),
            timestamp=airflow_event.end_date.timestamp(),
        )
    else:
        # Could also support timestamp override here; but would only benefit jobless Airlift.
        context.instance.report_runless_asset_event(
            asset_event=materialization,
        )


def _get_output_to_asset_key_map(
    context: OpExecutionContext, run: DagsterRun
) -> dict[AssetKey, str]:
    execution_plan_snap = context.instance.get_execution_plan_snapshot(
        check.not_none(run.execution_plan_snapshot_id)
    )
    mapping = {}
    for step in execution_plan_snap.steps:
        for output in step.outputs:
            props = check.not_none(output.properties)
            if props.asset_key:
                mapping[output.name] = props.asset_key
    return mapping


def _per_asset_metadata_from_run(
    context: OpExecutionContext, run: DagsterRun
) -> dict[AssetKey, dict[str, MetadataValue]]:
    output_to_key_map = _get_output_to_asset_key_map(context, run)
    conn = context.instance.event_log_storage.get_records_for_run(
        run_id=run.run_id,
        of_type=DagsterEventType.STEP_OUTPUT,
    )
    per_key_metadata = {}
    for event_record in conn.records:
        event = check.not_none(event_record.event_log_entry.dagster_event)
        if event.step_output_data.output_name in output_to_key_map:
            asset_key = output_to_key_map[event.step_output_data.output_name]
            if event.step_output_data.metadata:
                per_key_metadata[asset_key] = event.step_output_data.metadata
    return per_key_metadata
