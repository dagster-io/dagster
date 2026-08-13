from collections.abc import Iterator, Mapping, Sequence
from datetime import timedelta

from dagster import (
    AssetCheckEvaluation,
    AssetKey,
    AssetMaterialization,
    AssetObservation,
    DefaultSensorStatus,
    MetadataValue,
    SensorDefinition,
    SensorEvaluationContext,
    SensorResult,
    _check as check,
    sensor,
)
from dagster._core.definitions.repository_definition.repository_definition import (
    RepositoryDefinition,
)
from dagster._grpc.client import DEFAULT_SENSOR_GRPC_TIMEOUT
from dagster._record import record
from dagster._serdes import deserialize_value, serialize_value
from dagster._time import datetime_from_timestamp, get_current_datetime
from dagster_shared.serdes import whitelist_for_serdes

from dagster_dbt.cloud_v2.resources import DAGSTER_ADHOC_PREFIX, DbtCloudWorkspace
from dagster_dbt.cloud_v2.run_handler import (
    COMPLETED_AT_TIMESTAMP_METADATA_KEY,
    DbtCloudJobRunResults,
)
from dagster_dbt.cloud_v2.types import DbtCloudJob, DbtCloudRun
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator

MAIN_LOOP_TIMEOUT_SECONDS = DEFAULT_SENSOR_GRPC_TIMEOUT - 20
DEFAULT_DBT_CLOUD_SENSOR_INTERVAL_SECONDS = 30
START_LOOKBACK_SECONDS = 60  # Lookback one minute in time for the initial setting of the cursor.


@record
class BatchResult:
    idx: int
    asset_events: Sequence[AssetMaterialization]
    all_asset_keys_materialized: set[AssetKey]


def _job_asset_materialization_from_run(
    run: DbtCloudRun,
    job_asset_key: AssetKey,
) -> AssetMaterialization:
    """Emit a job-asset materialization for a finished Cloud run.

    Attaches run id, status, and Cloud run URL so users can click through from the
    Dagster materialization to the Cloud run page. Downstream ``AutomationCondition``s
    (e.g. ``eager()``) will fire on this materialization regardless of who kicked off
    the Cloud run — dbt Cloud UI, a Cloud schedule, or a Dagster-mirrored ``@job``.
    """
    metadata: dict[str, MetadataValue] = {
        "dbt_cloud_run_id": MetadataValue.int(run.id),
    }
    if run.status is not None:
        metadata["dbt_cloud_status"] = MetadataValue.text(run.status.name)
    if run.url:
        metadata["dbt_cloud_run_url"] = MetadataValue.url(run.url)
    return AssetMaterialization(asset_key=job_asset_key, metadata=metadata)


@whitelist_for_serdes
@record
class DbtCloudPollingSensorCursor:
    """A cursor that stores the last effective timestamp and offset."""

    finished_at_lower_bound: float | None = None
    finished_at_upper_bound: float | None = None
    offset: int | None = None


def materializations_from_batch_iter(
    context: SensorEvaluationContext,
    finished_at_lower_bound: float,
    finished_at_upper_bound: float,
    offset: int,
    workspace: DbtCloudWorkspace,
    dagster_dbt_translator: DagsterDbtTranslator,
    emit_job_asset_materializations: bool = False,
) -> Iterator[BatchResult | None]:
    client = workspace.get_client()
    workspace_data = workspace.get_or_fetch_workspace_data()

    # Build a set of all adhoc job IDs to filter out Dagster-triggered runs.
    # This includes the current adhoc job pool and any stale adhoc jobs from a
    # previous naming convention that still exist in dbt Cloud.
    adhoc_job_ids = {
        job["id"]
        for job in workspace_data.jobs
        if (job.get("name") or "").startswith(DAGSTER_ADHOC_PREFIX)
    }
    adhoc_job_ids.update(workspace_data.adhoc_job_ids)

    # Map each user-defined Cloud job id -> the AssetKey used when it's mirrored as
    # an asset. Adhoc jobs are excluded (they have no user-facing asset spec). Used
    # only when the caller opts into job-level materialization emission.
    job_key_by_id: Mapping[int, AssetKey] = (
        {
            job_details["id"]: DbtCloudJob.from_job_details(job_details).asset_key()
            for job_details in workspace_data.jobs
            if job_details.get("id") not in adhoc_job_ids
            and not (job_details.get("name") or "").startswith(DAGSTER_ADHOC_PREFIX)
        }
        if emit_job_asset_materializations
        else {}
    )

    total_processed_runs = 0
    while True:
        latest_offset = total_processed_runs + offset
        runs, total_runs = client.get_runs_batch(
            project_id=workspace.project_id,
            environment_id=workspace.environment_id,
            finished_at_lower_bound=datetime_from_timestamp(finished_at_lower_bound),
            finished_at_upper_bound=datetime_from_timestamp(finished_at_upper_bound),
            offset=latest_offset,
        )
        if len(runs) == 0:
            yield None
            context.log.info("Received no runs. Breaking.")
            break
        context.log.info(
            f"Processing {len(runs)}/{total_runs} runs for dbt Cloud "
            f"project {workspace.project_id} and environment {workspace.environment_id}..."
        )
        for i, run_details in enumerate(runs):
            run = DbtCloudRun.from_run_details(run_details=run_details)

            if run.job_definition_id in adhoc_job_ids:
                # Adhoc runs aren't user-facing Cloud jobs — always skip both
                # per-model AND job-level materializations for them.
                context.log.info(f"Run {run.id} was triggered by Dagster. Continuing.")
                continue

            # Job-level materialization for the mirrored Cloud job asset. Emitted
            # regardless of trigger source (Cloud UI, Cloud schedule, Dagster @job)
            # so downstream AutomationConditions can react uniformly.
            job_asset_events: list[AssetMaterialization] = []
            if emit_job_asset_materializations and run.job_definition_id in job_key_by_id:
                job_asset_events.append(
                    _job_asset_materialization_from_run(
                        run=run, job_asset_key=job_key_by_id[run.job_definition_id]
                    )
                )

            run_artifacts = client.list_run_artifacts(run_id=run.id)
            if "run_results.json" not in run_artifacts:
                context.log.info(
                    f"Run {run.id} does not have a run_results.json artifact. Continuing."
                )
                # Even without run_results.json we can still emit the job-level
                # materialization since the run itself finished.
                if job_asset_events:
                    yield BatchResult(
                        idx=i + latest_offset,
                        asset_events=job_asset_events,
                        all_asset_keys_materialized={mat.asset_key for mat in job_asset_events},
                    )
                else:
                    yield None
                continue

            run_results = DbtCloudJobRunResults.from_run_results_json(
                run_results_json=client.get_run_results_json(run_id=run.id)
            )
            events = run_results.to_default_asset_events(
                client=workspace.get_client(),
                manifest=workspace_data.manifest,
                dagster_dbt_translator=dagster_dbt_translator,
            )
            # Currently, only materializations are tracked
            mats = [event for event in events if isinstance(event, AssetMaterialization)]
            mats.extend(job_asset_events)
            context.log.info(f"Found {len(mats)} materializations for {run.id}")

            all_asset_keys_materialized = {mat.asset_key for mat in mats}
            yield (
                BatchResult(
                    idx=i + latest_offset,
                    asset_events=mats,
                    all_asset_keys_materialized=all_asset_keys_materialized,
                )
                if mats
                else None
            )
        total_processed_runs += len(runs)
        context.log.info(
            f"Processed {total_processed_runs}/{total_runs} runs for dbt Cloud "
            f"project {workspace.project_id} and environment {workspace.environment_id}..."
        )
        if total_processed_runs == total_runs:
            yield None
            context.log.info("Processed all runs. Breaking.")
            break


def sorted_asset_events(
    asset_events: Sequence[AssetMaterialization | AssetObservation | AssetCheckEvaluation],
    repository_def: RepositoryDefinition,
) -> list[AssetMaterialization | AssetObservation | AssetCheckEvaluation]:
    """Sort asset events by end date and toposort order."""
    topo_aks = repository_def.asset_graph.toposorted_asset_keys
    materializations_and_timestamps = [
        (mat.metadata[COMPLETED_AT_TIMESTAMP_METADATA_KEY].value, mat) for mat in asset_events
    ]
    return [
        sorted_event[1]
        for sorted_event in sorted(
            materializations_and_timestamps, key=lambda x: (topo_aks.index(x[1].asset_key), x[0])
        )
    ]


def build_dbt_cloud_polling_sensor(
    *,
    workspace: DbtCloudWorkspace,
    dagster_dbt_translator: DagsterDbtTranslator | None = None,
    minimum_interval_seconds: int = DEFAULT_DBT_CLOUD_SENSOR_INTERVAL_SECONDS,
    default_sensor_status: DefaultSensorStatus | None = None,
    emit_job_asset_materializations: bool = False,
) -> SensorDefinition:
    """The constructed sensor polls the dbt Cloud Workspace for activity, and inserts asset events into Dagster's event log.

    Args:
        workspace (DbtCloudWorkspace): The dbt Cloud workspace to poll for runs.
        dagster_dbt_translator (Optional[DagsterDbtTranslator], optional): The translator to use
            to convert dbt Cloud content into :py:class:`dagster.AssetSpec`.
            Defaults to :py:class:`DagsterDbtTranslator`.
        minimum_interval_seconds (int, optional): The minimum interval in seconds between sensor runs. Defaults to 30.
        default_sensor_status (Optional[DefaultSensorStatus], optional): The default status of the sensor.
        emit_job_asset_materializations (bool, optional): When ``True``, emit an
            :py:class:`AssetMaterialization` for each mirrored Cloud job asset when
            its Cloud run finishes (regardless of whether the run was triggered from
            Dagster, dbt Cloud UI, or a Cloud schedule). Used by
            :py:class:`DbtCloudComponent` when ``mirror_jobs`` includes ``asset``.

    Returns:
        Definitions: A `SensorDefinitions` object.
    """
    dagster_dbt_translator = dagster_dbt_translator or DagsterDbtTranslator()

    @sensor(
        name=f"dbt_cloud_{workspace.credentials.account_id}_{workspace.project_id}_{workspace.environment_id}__run_status_sensor",
        description=(
            f"dbt Cloud polling sensor for account {workspace.credentials.account_id}, "
            f"project {workspace.project_id} and environment {workspace.environment_id}"
        ),
        minimum_interval_seconds=minimum_interval_seconds,
        default_status=default_sensor_status or DefaultSensorStatus.RUNNING,
    )
    def dbt_cloud_run_sensor(context: SensorEvaluationContext) -> SensorResult:
        """Sensor to report materialization events for each asset as new runs come in."""
        context.log.info(
            f"Running sensor for dbt Cloud account {workspace.credentials.account_id}, "
            f"project {workspace.project_id} and environment {workspace.environment_id}"
        )
        try:
            cursor = (
                deserialize_value(context.cursor, DbtCloudPollingSensorCursor)
                if context.cursor
                else DbtCloudPollingSensorCursor()
            )
        except Exception as e:
            context.log.info(f"Failed to interpret cursor. Starting from scratch. Error: {e}")
            cursor = DbtCloudPollingSensorCursor()
        current_date = get_current_datetime()
        current_offset = cursor.offset or 0
        finished_at_lower_bound = (
            cursor.finished_at_lower_bound
            or (current_date - timedelta(seconds=START_LOOKBACK_SECONDS)).timestamp()
        )
        finished_at_upper_bound = cursor.finished_at_upper_bound or current_date.timestamp()
        sensor_iter = materializations_from_batch_iter(
            context=context,
            finished_at_lower_bound=finished_at_lower_bound,
            finished_at_upper_bound=finished_at_upper_bound,
            offset=current_offset,
            workspace=workspace,
            dagster_dbt_translator=dagster_dbt_translator,
            emit_job_asset_materializations=emit_job_asset_materializations,
        )

        all_asset_events: list[AssetMaterialization] = []
        latest_offset = current_offset
        repository_def = check.not_none(context.repository_def)
        batch_result = None
        while get_current_datetime() - current_date < timedelta(seconds=MAIN_LOOP_TIMEOUT_SECONDS):
            batch_result = next(sensor_iter, None)
            if batch_result is None:
                context.log.info("Received no batch result. Breaking.")
                break
            all_asset_events.extend(batch_result.asset_events)
            latest_offset = batch_result.idx

        if batch_result is not None:
            new_cursor = DbtCloudPollingSensorCursor(
                finished_at_lower_bound=finished_at_lower_bound,
                finished_at_upper_bound=finished_at_upper_bound,
                offset=latest_offset + 1,
            )
        else:
            # We have completed iteration for this range
            new_cursor = DbtCloudPollingSensorCursor(
                finished_at_lower_bound=finished_at_upper_bound,
                finished_at_upper_bound=None,
                offset=0,
            )

        context.update_cursor(serialize_value(new_cursor))

        context.log.info(
            f"Exiting sensor for dbt Cloud account {workspace.credentials.account_id}, "
            f"project {workspace.project_id} and environment {workspace.environment_id}"
        )
        return SensorResult(
            asset_events=sorted_asset_events(all_asset_events, repository_def),
        )

    return dbt_cloud_run_sensor
