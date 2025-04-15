from typing import Union

from dagster import RunRequest
from dagster._annotations import beta
from dagster._core.definitions.decorators.job_decorator import job
from dagster._core.definitions.decorators.op_decorator import op
from dagster._core.definitions.decorators.schedule_decorator import schedule
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.run_request import SkipReason
from dagster._core.definitions.schedule_definition import (
    DefaultScheduleStatus,
    ScheduleEvaluationContext,
)
from dagster._core.execution.context.op_execution_context import OpExecutionContext
from dagster._core.storage.dagster_run import RunsFilter
from dagster._grpc.client import DEFAULT_SENSOR_GRPC_TIMEOUT
from dagster._time import datetime_from_timestamp, get_current_datetime
from dagster_airlift.core.airflow_defs_data import AirflowDefinitionsData
from dagster_airlift.core.airflow_instance import AirflowInstance
from dagster_airlift.core.monitoring_job.event_stream import persist_events
from dagster_airlift.core.monitoring_job.utils import (
    augment_monitor_run_with_range_tags,
    get_range_from_run_history,
    structured_log,
)
from dagster_airlift.core.utils import monitoring_job_name

MAIN_LOOP_TIMEOUT_SECONDS = DEFAULT_SENSOR_GRPC_TIMEOUT - 20
DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS = 30
START_LOOKBACK_SECONDS = 60  # Lookback one minute in time for the initial setting of the cursor.


# IMPROVEME BCOR-102: We should be able to replace the sensor from the original Airlift functionality with this job.
@beta
def build_airflow_monitoring_defs(
    *,
    airflow_instance: AirflowInstance,
) -> Definitions:
    """The constructed job polls the Airflow instance for activity, and inserts asset events into Dagster's event log."""

    @job(name=monitoring_job_name(airflow_instance.name))
    def airflow_monitoring_job():
        _build_monitoring_op(airflow_instance)()

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


def _build_monitoring_op(
    airflow_instance: AirflowInstance,
) -> OpDefinition:
    @op(
        name=monitoring_job_op_name(airflow_instance),
    )
    def monitor_dags(context: OpExecutionContext) -> None:
        """The main function that runs the sensor. It polls the Airflow instance for activity and emits asset events."""
        # This is a hack to get the repository tag for the current run. It's bad because it assumes that the job we're
        # creating a run for is within the same repository; but I think that we'll have to do a second pass to get "outside of code
        # location" runs working (if that's even something we want to do).
        airflow_data = AirflowDefinitionsData(
            airflow_instance=airflow_instance, resolved_repository=context.repository_def
        )
        # get previously processed time range from run tags
        current_date = get_current_datetime()
        range_start, range_end = get_range_from_run_history(context, current_date.timestamp())
        augment_monitor_run_with_range_tags(context, range_start, range_end)

        structured_log(
            context,
            f"Processing from {datetime_from_timestamp(range_start)} to {datetime_from_timestamp(range_end)}",
        )
        persist_events(context, airflow_data, airflow_instance, range_start, range_end)

    return monitor_dags


def monitoring_job_op_name(airflow_instance: AirflowInstance) -> str:
    return f"core_monitor__{airflow_instance.name}"
