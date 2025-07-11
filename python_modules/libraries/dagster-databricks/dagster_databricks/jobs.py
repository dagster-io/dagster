"""Functionality to represent Databricks jobs in Dagster.

USAGE

    import os

    from dagster_databricks.jobs import build_databricks_job_defs
    from databricks.sdk import WorkspaceClient

    client = WorkspaceClient(
        host=os.environ.get("DATABRICKS_HOST"),
        token=os.environ.get("DATABRICKS_TOKEN"),
    )

    defs = build_databricks_job_defs(client)

"""

from datetime import datetime, timedelta, timezone
from typing import Union
from urllib.parse import urlparse

from dagster import JobDefinition, SensorDefinition, sensor
from dagster._annotations import preview
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.run_request import RunRequest, SkipReason
from dagster._core.definitions.sensor_definition import DefaultSensorStatus, SensorEvaluationContext
from dagster._core.definitions.utils import VALID_NAME_REGEX
from dagster._core.events import DagsterEvent
from dagster._core.remote_representation.origin import RemoteJobOrigin, RemoteRepositoryOrigin
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus
from dagster._core.storage.tags import EXTERNAL_JOB_SOURCE_TAG_KEY
from dagster._core.utils import make_new_run_id
from dagster._record import record
from dagster._serdes import deserialize_value, serialize_value
from dagster._time import get_current_datetime
from dagster_shared.serdes import whitelist_for_serdes
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.jobs import BaseJob, RunLifeCycleState, RunResultState

NO_CURSOR_LOOKBACK_DELTA = timedelta(days=7)


# TODO- refactor from shared method in `dagster-airlift`
def normalize_dagster_name(name: str) -> str:
    """Converts a name to a valid dagster name by replacing invalid characters with underscores. / is converted to a double underscore."""
    return "".join(c if VALID_NAME_REGEX.match(c) else "__" if c == "/" else "_" for c in name)


def normalize_job_id(job: BaseJob) -> str:
    # name=normalize_dagster_name(job.settings.name or str(job.job_id)),
    return str(job.job_id)


def construct_external_databricks_jobs(client: "WorkspaceClient"):
    jobs = [
        JobDefinition.for_external_job(
            name=normalize_job_id(job),
            asset_keys=[],
            metadata={
                "job_settings_name": job.settings.name,
                "job_settings_max_concurrent_runs": job.settings.max_concurrent_runs,
            },
            tags=job.settings.tags,
        )
        for job in client.jobs.list()
        if job and job.job_id
    ]
    return jobs


def databricks_host_name(host: str) -> str:
    """Extract name from Databricks host.

    Given the `host` https://abc-1234-wxyz.cloud.databricks.com" returns abc-1234-wxyz.
    """
    parsed = urlparse(host)
    hostname = parsed.hostname or parsed.path
    return hostname.split(".")[0]


@whitelist_for_serdes
@record
class DatabricksJobSensorCursor:
    range_start: str
    range_end: str

    @property
    def range_start_utc_ms(self) -> int:
        return int(datetime.fromisoformat(self.range_start).timestamp() * 1000)

    @property
    def range_end_utc_ms(self) -> int:
        return int(datetime.fromisoformat(self.range_end).timestamp() * 1000)

    def advance(self, effective_timestamp: datetime) -> "DatabricksJobSensorCursor":
        return DatabricksJobSensorCursor(
            range_start=self.range_end, range_end=effective_timestamp.isoformat()
        )


# TODO- consider lazy evaluation
@preview
def build_databricks_job_defs(client: WorkspaceClient) -> Definitions:
    return Definitions(
        jobs=construct_external_databricks_jobs(client),
        sensors=[build_databricks_jobs_monitor_sensor(client)],
    )


@preview
def build_databricks_jobs_monitor_sensor(client: WorkspaceClient) -> SensorDefinition:
    """Creates a sensor that polls Databricks jobs, and serializes their status on the cursor."""
    databricks_name = normalize_dagster_name(databricks_host_name(client.config.host))

    @sensor(
        name=f"{databricks_name}__databricks_jobs_monitor_sensor",
        default_status=DefaultSensorStatus.RUNNING,
    )
    def databricks_job_sensor(
        context: SensorEvaluationContext,
    ) -> Union[RunRequest, SkipReason]:
        context.log.info(
            f"************Polling Databricks jobs on host {client.config.host}***********"
        )
        effective_timestamp = get_current_datetime()
        if context.cursor is None:
            cursor = DatabricksJobSensorCursor(
                range_start=(get_current_datetime() - NO_CURSOR_LOOKBACK_DELTA).isoformat(),
                range_end=effective_timestamp.isoformat(),
            )
        else:
            cursor = deserialize_value(context.cursor, DatabricksJobSensorCursor)

        context.log.info(
            f"Polling for jobs within the range {cursor.range_start} and {cursor.range_end}"
        )

        # NOTE- we can either get all job runs from `list_runs` or get the runs for a particular job
        # by providing the `job_id` parameter. Currently, we first get the job IDs, and then the
        # runs for each job to make it easier to support job filters in a future implementation.
        for job in client.jobs.list():
            runs = client.jobs.list_runs(
                job_id=job.job_id,
                start_time_from=cursor.range_start_utc_ms,
                start_time_to=cursor.range_end_utc_ms,
            )
            # TODO- handle backfilling of run history
            # TODO- ensure run is most recent
            run = next(iter(runs), None)

            # TODO- handle pending
            # see: dagster_airlift/core/monitoring_job/event_stream.py
            if run:
                if run.state and run.state.life_cycle_state == RunLifeCycleState.TERMINATED:
                    dagster_job_name = normalize_job_id(job)
                    dagster_run_id = make_new_run_id()

                    run_start_time_dt = datetime.fromtimestamp(
                        run.start_time / 1000.0, tz=timezone.utc
                    )
                    run_end_time_dt = datetime.fromtimestamp(run.end_time / 1000.0, tz=timezone.utc)

                    context.instance.run_storage.add_historical_run(
                        dagster_run=DagsterRun(
                            run_id=dagster_run_id,
                            job_name=dagster_job_name,
                            status=DagsterRunStatus.NOT_STARTED,
                            tags={
                                "dagster-databricks/job-id": str(run.job_id),
                                "dagster-databricks/job-run-id": str(run.run_id),
                                EXTERNAL_JOB_SOURCE_TAG_KEY: "databricks",
                            },
                            # Setting `remote_job_origin` is required to link the run back to
                            # the job in the `Runs` tab of the UI.
                            remote_job_origin=RemoteJobOrigin(
                                repository_origin=RemoteRepositoryOrigin(
                                    repository_name=context.repository_name,
                                    code_location_origin=context.code_location_origin,
                                ),
                                job_name=dagster_job_name,
                            ),
                        ),
                        run_creation_time=run_start_time_dt,
                    )

                    context.instance.report_dagster_event(
                        run_id=dagster_run_id,
                        dagster_event=DagsterEvent(
                            event_type_value="PIPELINE_START",
                            job_name=dagster_job_name,
                        ),
                        timestamp=run_start_time_dt.timestamp(),
                    )

                    if run.state.result_state == RunResultState.SUCCESS:
                        context.instance.report_dagster_event(
                            run_id=dagster_run_id,
                            dagster_event=DagsterEvent(
                                event_type_value="PIPELINE_SUCCESS",
                                job_name=dagster_job_name,
                            ),
                            timestamp=run_end_time_dt.timestamp(),
                        )

                    elif run.state.result_state == RunResultState.FAILED:
                        context.instance.report_dagster_event(
                            run_id=dagster_run_id,
                            dagster_event=DagsterEvent(
                                event_type_value="PIPELINE_FAILURE",
                                job_name=normalize_job_id(job),
                            ),
                            timestamp=run_end_time_dt.timestamp(),
                        )

        cursor = cursor.advance(effective_timestamp)
        context.update_cursor(serialize_value(cursor))

    return databricks_job_sensor
