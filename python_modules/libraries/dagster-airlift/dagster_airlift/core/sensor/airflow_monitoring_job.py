import time
from typing import Union

from dagster import AssetMaterialization, RunRequest
from dagster._annotations import beta
from dagster._core.definitions.decorators.job_decorator import job
from dagster._core.definitions.decorators.op_decorator import op
from dagster._core.definitions.decorators.schedule_decorator import schedule
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.reconstruct import ReconstructableJob
from dagster._core.definitions.run_request import SkipReason
from dagster._core.definitions.schedule_definition import (
    DefaultScheduleStatus,
    ScheduleEvaluationContext,
)
from dagster._core.errors import DagsterUserCodeExecutionError
from dagster._core.events import (
    AssetMaterializationPlannedData,
    DagsterEvent,
    JobFailureData,
    StepMaterializationData,
)
from dagster._core.execution.context.op_execution_context import OpExecutionContext
from dagster._core.origin import JobPythonOrigin
from dagster._core.remote_representation.origin import RemoteJobOrigin
from dagster._core.storage.dagster_run import DagsterRunStatus, RunsFilter
from dagster._core.storage.tags import REPOSITORY_LABEL_TAG
from dagster._core.utils import make_new_run_id
from dagster._grpc.client import DEFAULT_SENSOR_GRPC_TIMEOUT
from dagster._time import datetime_from_timestamp, get_current_datetime

from dagster_airlift.constants import DAG_ID_TAG_KEY, DAG_RUN_ID_TAG_KEY
from dagster_airlift.core.airflow_defs_data import AirflowDefinitionsData
from dagster_airlift.core.airflow_instance import AirflowInstance
from dagster_airlift.core.utils import AIRFLOW_RUN_STATE_TO_DAGSTER_RUN_STATUS, monitoring_job_name

MAIN_LOOP_TIMEOUT_SECONDS = DEFAULT_SENSOR_GRPC_TIMEOUT - 20
DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS = 30
START_LOOKBACK_SECONDS = 60  # Lookback one minute in time for the initial setting of the cursor.


class AirliftSensorEventTransformerError(DagsterUserCodeExecutionError):
    """Error raised when an error occurs in the event transformer function."""


# We should be able to completely replace the sensor with this. It's just better in every way.
@beta
def build_airflow_monitoring_defs(
    *,
    airflow_instance: AirflowInstance,
) -> Definitions:
    """The constructed job polls the Airflow instance for activity, and inserts asset events into Dagster's event log."""

    @op(
        name=f"{airflow_instance.name}__airflow_dag_status_sensor",
    )
    def monitor_dags(context: OpExecutionContext) -> None:
        """The main function that runs the sensor. It polls the Airflow instance for activity and emits asset events."""
        # This is a hack to get the repository tag for the current run. It's bad because it assumes that the job we're
        # creating a run for is within the same repository; but I think that we'll have to do a second pass to get "outside of code
        # location" runs working (if that's even something we want to do).
        repo_label = context.run.tags_for_storage()[REPOSITORY_LABEL_TAG]
        airflow_data = AirflowDefinitionsData(
            airflow_instance=airflow_instance, resolved_repository=context.repository_def
        )
        # get previously processed time range from run tags
        current_date = get_current_datetime()
        prev_run = next(
            iter(
                context.instance.get_runs(
                    filters=RunsFilter(
                        job_name=context.job_name, statuses=[DagsterRunStatus.SUCCESS]
                    ),
                    limit=1,
                )
            ),
            None,
        )
        if prev_run:
            # Start from the end of the last run
            range_start = float(prev_run.tags_for_storage()["dagster-airlift/monitoring_job_range_end"])
        else:
            range_start = current_date.timestamp() - START_LOOKBACK_SECONDS
        range_end = current_date.timestamp()
        context.instance.add_run_tags(
            run_id=context.run_id,
            new_tags={
                "dagster-airlift/monitoring_job_range_start": str(range_start),
                "dagster-airlift/monitoring_job_range_end": str(range_end),
            },
        )
        context.log.info(
            f"Airflow Monitoring Job: Processing from {datetime_from_timestamp(range_start)} to {datetime_from_timestamp(range_end)}"
        )

        offset = 0

        job_dag_ids = {
            dag_handle.dag_id
            for dag_handle in airflow_data.airflow_mapped_jobs_by_dag_handle.keys()
        }
        dag_ids_with_assets = airflow_data.dag_ids_with_mapped_asset_keys

        context.log.info(
            f"Processing runs started within time range {datetime_from_timestamp(range_start)} to {datetime_from_timestamp(range_end)}"
        )
        while True:
            (newly_started_runs, total_entries) = airflow_instance.get_dag_runs_batch(
                states=["running", "queued"],
                # When monitoring started runs; we only need to monitor dags that have an associated job.
                dag_ids=list(job_dag_ids),
                start_date_gte=datetime_from_timestamp(range_start),
                start_date_lte=datetime_from_timestamp(range_end),
                offset=offset,
            )
            context.log.info(
                f"Found {len(newly_started_runs)} newly started runs in the time range {datetime_from_timestamp(range_start)} to {datetime_from_timestamp(range_end)}"
            )
            for run in newly_started_runs:
                run_id = make_new_run_id()
                job_def = airflow_data.airflow_mapped_jobs_by_dag_handle[run.dag_handle]
                context.instance.create_run_for_job(
                    run_id=run_id,
                    job_def=job_def,
                    tags={
                        DAG_RUN_ID_TAG_KEY: run.run_id,
                        DAG_ID_TAG_KEY: run.dag_id,
                        REPOSITORY_LABEL_TAG: repo_label,
                        "FAKE_TAG": repo_label,
                    },
                    status=DagsterRunStatus.NOT_STARTED,
                )
                # Emit a Dagster event for the run.
                context.instance.report_dagster_event(
                    run_id=run_id,
                    dagster_event=DagsterEvent(
                        event_type_value="PIPELINE_START",
                        job_name=job_def.name,
                    )
                )
                # Emit asset planned materializations for the run.
                # We probably want to standardize these "external job emission" pathways.
                for asset in airflow_data.assets_per_job[job_def.name]:
                    context.instance.report_dagster_event(
                        run_id=run_id,
                        dagster_event=DagsterEvent.build_asset_materialization_planned_event(
                            job_name=job_def.name,
                            asset_materialization_planned_data=AssetMaterializationPlannedData(
                                asset_key=asset,
                            ),
                            # Will this cause problems?
                            step_key="",
                        ),
                    )
            offset += len(newly_started_runs)
            context.log.info(
                f"Finished processing {offset} / {total_entries} newly started runs in the time range {datetime_from_timestamp(range_start)} to {datetime_from_timestamp(range_end)}"
            )
            if offset >= total_entries:
                break
        
        offset = 0
        while True:
            # Finally, process completed dag runs.
            newly_completed_runs, total_entries = airflow_instance.get_dag_runs_batch(
                states=["success", "failed", "up_for_retry"],
                dag_ids=list(job_dag_ids.union(dag_ids_with_assets)),
                start_date_gte=datetime_from_timestamp(range_start),
                start_date_lte=datetime_from_timestamp(range_end),
                offset=offset,
            )
            for run in newly_completed_runs:
                corresponding_dagster_run = next(
                    iter(
                        context.instance.get_runs(
                            filters=RunsFilter(
                                tags={DAG_RUN_ID_TAG_KEY: run.run_id, DAG_ID_TAG_KEY: run.dag_id}
                            ),
                        )
                    ),
                    None,
                )
                job_def = airflow_data.airflow_mapped_jobs_by_dag_handle.get(run.dag_handle)
                if job_def and corresponding_dagster_run is None:
                    context.log.info(
                        f"Airflow Monitoring Job: No corresponding Dagster run found for completed Airflow run {run.run_id}. Creating a new run."
                    )
                    # If there's no corresponding run but there is an associated job, it's possible that the run started and completed within the same iteration.
                    # So we need to create a new run for it.
                    # TODO: We need to also handle "history" here. Specifically, mapping out the timestamps of events correctly.
                    # Right now, this is just going to show up as a "blip".
                    # What we need to do is set the repository tag here. I think the easiest way to do this is going to be via graphql.
                    # step_execution_context = context.get_step_execution_context()
                    # job = step_execution_context.plan_data.job
                    # origin = JobPythonOrigin(job_name=job_def.name, repository_origin=job.repository.get_python_origin()) if isinstance(job, ReconstructableJob) else None
                    run_id = make_new_run_id()
                    corresponding_dagster_run = context.instance.create_run_for_job(
                        run_id=run_id,
                        job_def=job_def,
                        tags={
                            DAG_RUN_ID_TAG_KEY: run.run_id,
                            DAG_ID_TAG_KEY: run.dag_id,
                            REPOSITORY_LABEL_TAG: repo_label,
                            "FAKE_TAG": repo_label,
                        },
                        status=DagsterRunStatus.NOT_STARTED,
                    )
                    # Emit a Dagster event for the run.
                    context.instance.report_dagster_event(
                        run_id=run_id,
                        dagster_event=DagsterEvent(
                            event_type_value="PIPELINE_START",
                            job_name=job_def.name,
                        )
                    )
                    # We really need to handle the timeline stuff here.
                    time.sleep(1)
                    context.log.info(
                        f"Airflow Monitoring Job: Created a new Dagster run {run_id} for completed Airflow run {run.run_id}."
                    )
                # Emit asset materialization events for assets which are mapped to the entire dag.
                for asset in airflow_data.all_asset_keys_by_dag_handle[run.dag_handle]:
                    # If there's a corresponding run, emit events for that run.
                    if corresponding_dagster_run:
                        context.instance.report_dagster_event(
                            run_id=corresponding_dagster_run.run_id,
                            dagster_event=DagsterEvent(
                                event_type_value="ASSET_MATERIALIZATION",
                                job_name=corresponding_dagster_run.job_name,
                                event_specific_data=StepMaterializationData(
                                    materialization=AssetMaterialization(
                                        asset_key=asset,
                                    ),
                                ),
                            ),
                        )
                    else:
                        # Need to go back and embellish with metadata
                        context.instance.report_runless_asset_event(
                            asset_event=AssetMaterialization(
                                asset_key=asset,
                            )
                        )

                if corresponding_dagster_run is None:
                    # TODO: Actually what we want to do here is emit EVERYTHING, assuming there's a corresponding job. Bc this is the case where the run completed between iterations.
                    context.log.warning(
                        f"Airflow Monitoring Job: No corresponding Dagster run found for completed Airflow run {run.run_id}. Skipping run event emission."
                    )
                    continue
                if run.state == "success":
                    context.log.info(
                        f"Airflow Monitoring Job: Emitting pipeline success event for run {run.run_id}."
                    )
                    event = DagsterEvent(
                        event_type_value="PIPELINE_SUCCESS",
                        job_name=job_def.name,
                    )
                else:
                    context.log.info(
                        f"Airflow Monitoring Job: Emitting pipeline failure event for run {run.run_id}."
                    )
                    event = DagsterEvent(
                        event_type_value="PIPELINE_FAILURE",
                        job_name=job_def.name,
                        event_specific_data=JobFailureData(
                            error=None, failure_reason=None, first_step_failure_event=None
                        ),
                    )
                context.instance.report_dagster_event(
                    run_id=corresponding_dagster_run.run_id, dagster_event=event
                )
            offset += len(newly_completed_runs)
            context.log.info(
                f"Finished processing {offset} / {total_entries} completed runs in the time range {datetime_from_timestamp(range_start)} to {datetime_from_timestamp(range_end)}"
            )
            if offset >= total_entries:
                break

        # Then, process completed successful task instances.
        # You'll notice that the query pattern here is different from the dag run query pattern.
        # That's because early Airflow 2 versions don't support batch size queries for task instances.
        # NOTE: In the case where we have a run which completed between iterations, we'll be emitting events for the run _after_ we've marked the run as finished.
        # so the timeline will be a bit screwed up.
        task_instances = airflow_instance.get_task_instance_batch_time_range(
            states=["success"],
            dag_ids=list(job_dag_ids.union(dag_ids_with_assets)),
            end_date_gte=datetime_from_timestamp(range_start),
            end_date_lte=datetime_from_timestamp(range_end),
        )
        context.log.info(
            f"Found {len(task_instances)} completed task instances in the time range {datetime_from_timestamp(range_start)} to {datetime_from_timestamp(range_end)}"
        )

        for task_instance in task_instances:
            corresponding_dagster_run = next(
                iter(
                    context.instance.get_runs(
                        filters=RunsFilter(
                            tags={
                                DAG_RUN_ID_TAG_KEY: task_instance.run_id,
                                DAG_ID_TAG_KEY: task_instance.dag_id,
                            }
                        ),
                    )
                ),
                None,
            )
            context.log.info(
                f"Processing task instance {task_instance.task_id} for dag {task_instance.dag_id}"
            )
            for asset in airflow_data.mapped_asset_keys_by_task_handle[task_instance.task_handle]:
                # If there's a corresponding run, emit events for that run.
                if corresponding_dagster_run:
                    context.instance.report_dagster_event(
                        run_id=corresponding_dagster_run.run_id,
                        dagster_event=DagsterEvent(
                            event_type_value="ASSET_MATERIALIZATION",
                            job_name=corresponding_dagster_run.job_name,
                            event_specific_data=StepMaterializationData(
                                materialization=AssetMaterialization(
                                    asset_key=asset,
                                ),
                            ),
                        ),
                    )
                else:
                    # Need to go back and embellish with metadata
                    context.instance.report_runless_asset_event(
                        asset_event=AssetMaterialization(
                            asset_key=asset,
                        )
                    )
            context.log.info(
                f"Emitted {len(airflow_data.mapped_asset_keys_by_task_handle[task_instance.task_handle])} materializations for task instance {task_instance.task_id} in dag {task_instance.dag_id}."
            )

        context.log.info(
            f"Airflow Monitoring Job: Finished processing from {datetime_from_timestamp(range_start)} to {datetime_from_timestamp(range_end)}"
        )

    @job(name=monitoring_job_name(airflow_instance.name))
    def airflow_monitoring_job():
        monitor_dags()

    @schedule(
        job=airflow_monitoring_job,
        cron_schedule="* * * * *",
        name=f"{airflow_instance.name}__airflow_monitoring_job_schedule",
        default_status=DefaultScheduleStatus.RUNNING,
    )
    def airflow_monitoring_job_schedule(
        context: ScheduleEvaluationContext,
    ) -> Union[RunRequest, SkipReason]:
        """The schedule that runs the sensor job."""
        # Get the last run for this job
        last_run = next(
            iter(
                context.instance.get_runs(
                    filters=RunsFilter(job_name=airflow_monitoring_job.name),
                    limit=1,
                )
            ),
            None,
        )
        if not last_run or last_run.is_finished:
            return RunRequest()
        else:
            return SkipReason("Monitoring job is already running.")

    return Definitions(
        jobs=[airflow_monitoring_job],
        schedules=[airflow_monitoring_job_schedule],
    )
