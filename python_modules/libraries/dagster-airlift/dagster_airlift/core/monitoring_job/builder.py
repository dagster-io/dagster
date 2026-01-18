import datetime
from typing import Optional, Union

from dagster import RunRequest, sensor
from dagster._annotations import beta
from dagster._config.pythonic_config.config import Config
from dagster._core.definitions.decorators.job_decorator import job
from dagster._core.definitions.decorators.op_decorator import op
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.run_config import RunConfig
from dagster._core.definitions.run_request import SkipReason
from dagster._core.definitions.sensor_definition import (
    DefaultSensorStatus,
    SensorDefinition,
    SensorEvaluationContext,
)
from dagster._core.execution.context.op_execution_context import OpExecutionContext
from dagster._core.storage.dagster_run import DagsterRun, RunsFilter
from dagster._daemon.auto_run_reexecution.auto_run_reexecution import run_was_successfully_retried
from dagster._grpc.client import DEFAULT_SENSOR_GRPC_TIMEOUT
from dagster._record import record
from dagster._serdes import deserialize_value, serialize_value
from dagster._time import get_current_datetime
from dagster_shared.serdes import whitelist_for_serdes
from pydantic import Field

from dagster_airlift.core.airflow_defs_data import AirflowDefinitionsData
from dagster_airlift.core.airflow_instance import AirflowInstance
from dagster_airlift.core.monitoring_job.event_stream import persist_events
from dagster_airlift.core.monitoring_job.utils import structured_log
from dagster_airlift.core.utils import monitoring_job_name

MAIN_LOOP_TIMEOUT_SECONDS = DEFAULT_SENSOR_GRPC_TIMEOUT - 20
DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS = 30
NO_CURSOR_LOOKBACK_DELTA = datetime.timedelta(days=1)


@whitelist_for_serdes
@record
class AirflowMonitoringJobSensorCursor:
    range_start: str
    range_end: str

    def to_config(self) -> "MonitoringConfig":
        return MonitoringConfig(range_start=self.range_start, range_end=self.range_end)

    def to_tags(self) -> dict[str, str]:
        return {
            "range_start": self.range_start,
            "range_end": self.range_end,
        }

    def advance(self, effective_timestamp: datetime.datetime) -> "AirflowMonitoringJobSensorCursor":
        return AirflowMonitoringJobSensorCursor(
            range_start=self.range_end, range_end=effective_timestamp.isoformat()
        )


# IMPROVEME BCOR-102: We should be able to replace the sensor from the original Airlift functionality with this job.
@beta
def build_airflow_monitoring_defs(
    *,
    airflow_instance: AirflowInstance,
) -> Definitions:
    """The constructed job polls the Airflow instance for activity, and inserts asset events into Dagster's event log."""
    return Definitions(
        jobs=[build_monitoring_job(airflow_instance=airflow_instance)],
        sensors=[build_monitoring_sensor(airflow_instance=airflow_instance)],
    )


class MonitoringConfig(Config):
    range_start: str = Field(
        description="The start of the range to process. Should be an ISO 8601 formatted string."
    )
    range_end: str = Field(
        description="The end of the range to process. Should be an ISO 8601 formatted string."
    )

    @property
    def range_start_datetime(self) -> datetime.datetime:
        return datetime.datetime.fromisoformat(self.range_start)

    @property
    def range_end_datetime(self) -> datetime.datetime:
        return datetime.datetime.fromisoformat(self.range_end)


def build_monitoring_sensor(
    *,
    airflow_instance: AirflowInstance,
) -> SensorDefinition:
    @sensor(
        job_name=monitoring_job_name(airflow_instance.name),
        name=f"{airflow_instance.name}__airflow_monitoring_job_sensor",
        default_status=DefaultSensorStatus.RUNNING,
    )
    def airflow_monitoring_job_sensor(
        context: SensorEvaluationContext,
    ) -> Union[RunRequest, SkipReason]:
        effective_timestamp = get_current_datetime()
        if context.cursor is None:
            cursor = AirflowMonitoringJobSensorCursor(
                range_start=(get_current_datetime() - NO_CURSOR_LOOKBACK_DELTA).isoformat(),
                range_end=effective_timestamp.isoformat(),
            )
        else:
            cursor = deserialize_value(context.cursor, AirflowMonitoringJobSensorCursor)

        run = _get_run_for_cursor(context, airflow_instance, cursor)
        # We only advance the cursor if the run has finished successfully.
        if run and not run.is_finished:
            return SkipReason(
                f"Monitoring job is still running for range {cursor.range_start} to {cursor.range_end}. Waiting to advance."
            )
        if run and not run.is_success and not run_was_successfully_retried(run, context.instance):
            raise Exception(
                f"Monitoring job failed for range {cursor.range_start} to {cursor.range_end} with run {run.run_id}. Dagster currently expects runs to be inserted in time-increasing order. To avoid unexpected side effects, the sensor will wait until this range has been successfully executed before advancing. To rectify this, you can either wait for automatic retries to succeed, or you can manually re-execute the failed run once the issue is resolved."
            )
        cursor = cursor if not run else cursor.advance(effective_timestamp)
        context.update_cursor(serialize_value(cursor))

        return RunRequest(
            run_config=RunConfig(
                ops={monitoring_job_op_name(airflow_instance): cursor.to_config()},
            ),
            tags=cursor.to_tags(),
        )

    return airflow_monitoring_job_sensor


def _get_run_for_cursor(
    context: SensorEvaluationContext,
    airflow_instance: AirflowInstance,
    cursor: AirflowMonitoringJobSensorCursor,
) -> Optional[DagsterRun]:
    return next(
        iter(
            context.instance.get_runs(
                filters=RunsFilter(
                    job_name=monitoring_job_name(airflow_instance.name), tags=cursor.to_tags()
                ),
                limit=1,
            )
        ),
        None,
    )


def _build_monitoring_op(
    airflow_instance: AirflowInstance,
) -> OpDefinition:
    @op(
        name=monitoring_job_op_name(airflow_instance),
    )
    def monitor_dags(context: OpExecutionContext, config: MonitoringConfig) -> None:
        """The main function that runs the sensor. It polls the Airflow instance for activity and emits asset events."""
        # This is a hack to get the repository tag for the current run. It's bad because it assumes that the job we're
        # creating a run for is within the same repository; but I think that we'll have to do a second pass to get "outside of code
        # location" runs working (if that's even something we want to do).
        airflow_data = AirflowDefinitionsData(
            airflow_instance=airflow_instance, resolved_repository=context.repository_def
        )

        structured_log(
            context,
            f"Processing from {config.range_start} to {config.range_end}",
        )
        persist_events(
            context,
            airflow_data,
            airflow_instance,
            config.range_start_datetime.timestamp(),
            config.range_end_datetime.timestamp(),
        )

    return monitor_dags


def monitoring_job_op_name(airflow_instance: AirflowInstance) -> str:
    return f"core_monitor__{airflow_instance.name}"


def build_monitoring_job(
    *,
    airflow_instance: AirflowInstance,
) -> JobDefinition:
    @job(name=monitoring_job_name(airflow_instance.name))
    def airflow_monitoring_job():
        _build_monitoring_op(airflow_instance)()

    return airflow_monitoring_job
