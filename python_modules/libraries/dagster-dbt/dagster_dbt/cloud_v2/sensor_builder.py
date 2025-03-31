from collections.abc import Iterator, Sequence
from datetime import timedelta
from typing import Optional, Union

from dagster import (
    AssetCheckEvaluation,
    AssetKey,
    AssetMaterialization,
    AssetObservation,
    DefaultSensorStatus,
    SensorDefinition,
    SensorEvaluationContext,
    SensorResult,
    _check as check,
    sensor,
)
from dagster._annotations import preview
from dagster._core.definitions.repository_definition.repository_definition import (
    RepositoryDefinition,
)
from dagster._grpc.client import DEFAULT_SENSOR_GRPC_TIMEOUT
from dagster._record import record
from dagster._serdes import deserialize_value, serialize_value
from dagster._time import datetime_from_timestamp, get_current_datetime
from dagster_shared.serdes import whitelist_for_serdes

from dagster_dbt.cloud_v2.resources import DbtCloudWorkspace
from dagster_dbt.cloud_v2.run_handler import (
    COMPLETED_AT_TIMESTAMP_METADATA_KEY,
    DbtCloudJobRunResults,
)
from dagster_dbt.cloud_v2.types import DbtCloudRun
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator

MAIN_LOOP_TIMEOUT_SECONDS = DEFAULT_SENSOR_GRPC_TIMEOUT - 20
DEFAULT_DBT_CLOUD_SENSOR_INTERVAL_SECONDS = 30
START_LOOKBACK_SECONDS = 60  # Lookback one minute in time for the initial setting of the cursor.


@record
class BatchResult:
    idx: int
    asset_events: Sequence[AssetMaterialization]
    all_asset_keys_materialized: set[AssetKey]


@whitelist_for_serdes
@record
class DbtCloudPollingSensorCursor:
    """A cursor that stores the last effective timestamp and offset."""

    finished_at_lower_bound: Optional[float] = None
    finished_at_upper_bound: Optional[float] = None
    offset: Optional[int] = None


def materializations_from_batch_iter(
    context: SensorEvaluationContext,
    finished_at_lower_bound: float,
    finished_at_upper_bound: float,
    offset: int,
    workspace: DbtCloudWorkspace,
    dagster_dbt_translator: DagsterDbtTranslator,
) -> Iterator[Optional[BatchResult]]:
    client = workspace.get_client()

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
            f"Processing {len(runs)}/{total_runs} runs for dbt Cloud workspace "
            f"for project {workspace.project_name} and environment {workspace.environment_name}..."
        )
        for i, run_details in enumerate(runs):
            run = DbtCloudRun.from_run_details(run_details=run_details)

            run_artifacts = client.list_run_artifacts(run_id=run.id)
            if "run_results.json" not in run_artifacts:
                context.log.info(
                    f"Run {run.id} does not have a run_results.json artifact. Continuing."
                )
                continue

            run_results = DbtCloudJobRunResults.from_run_results_json(
                run_results_json=client.get_run_results_json(run_id=run.id)
            )
            events = run_results.to_default_asset_events(
                client=workspace.get_client(),
                manifest=workspace.fetch_workspace_data().manifest,
                dagster_dbt_translator=dagster_dbt_translator,
            )
            # Currently, only materializations are tracked
            mats = [event for event in events if isinstance(event, AssetMaterialization)]
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
            f"Processed {total_processed_runs}/{total_runs} runs for dbt Cloud workspace "
            f"for project {workspace.project_name} and environment {workspace.environment_name}..."
        )
        if total_processed_runs == total_runs:
            yield None
            context.log.info("Processed all runs. Breaking.")
            break


def sorted_asset_events(
    asset_events: Sequence[Union[AssetMaterialization, AssetObservation, AssetCheckEvaluation]],
    repository_def: RepositoryDefinition,
) -> list[Union[AssetMaterialization, AssetObservation, AssetCheckEvaluation]]:
    """Sort asset events by end date and toposort order."""
    topo_aks = repository_def.asset_graph.toposorted_asset_keys
    materializations_and_timestamps = [
        (mat.metadata[COMPLETED_AT_TIMESTAMP_METADATA_KEY].value, mat) for mat in asset_events
    ]
    return [
        sorted_event[1]
        for sorted_event in sorted(
            materializations_and_timestamps, key=lambda x: (x[0], topo_aks.index(x[1].asset_key))
        )
    ]


@preview
def build_dbt_cloud_polling_sensor(
    *,
    workspace: DbtCloudWorkspace,
    dagster_dbt_translator: Optional[DagsterDbtTranslator] = None,
    minimum_interval_seconds: int = DEFAULT_DBT_CLOUD_SENSOR_INTERVAL_SECONDS,
    default_sensor_status: Optional[DefaultSensorStatus] = None,
) -> SensorDefinition:
    """The constructed sensor polls the dbt Cloud Workspace for activity, and inserts asset events into Dagster's event log.

    Args:
        workspace (DbtCloudWorkspace): The dbt Cloud workspace to poll for runs.
        dagster_dbt_translator (Optional[DagsterDbtTranslator], optional): The translator to use
            to convert dbt Cloud content into :py:class:`dagster.AssetSpec`.
            Defaults to :py:class:`DagsterDbtTranslator`.
        minimum_interval_seconds (int, optional): The minimum interval in seconds between sensor runs. Defaults to 30.
        default_sensor_status (Optional[DefaultSensorStatus], optional): The default status of the sensor.

    Returns:
        Definitions: A `Definitions` object containing the constructed sensor.
    """
    dagster_dbt_translator = dagster_dbt_translator or DagsterDbtTranslator()

    @sensor(
        name=f"{workspace.account_name}_{workspace.project_name}_{workspace.environment_name}__run_status_sensor",
        minimum_interval_seconds=minimum_interval_seconds,
        default_status=default_sensor_status or DefaultSensorStatus.RUNNING,
    )
    def dbt_cloud_run_sensor(context: SensorEvaluationContext) -> SensorResult:
        """Sensor to report materialization events for each asset as new runs come in."""
        context.log.info(
            f"************"
            f"Running sensor for dbt Cloud workspace for account {workspace.account_name}, "
            f"project {workspace.project_name} and environment {workspace.environment_name}"
            f"***********"
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
            f"************"
            f"Exiting sensor for dbt Cloud workspace for account {workspace.account_name}, "
            f"project {workspace.project_name} and environment {workspace.environment_name}"
            f"***********"
        )
        return SensorResult(
            asset_events=sorted_asset_events(all_asset_events, repository_def),
        )

    return dbt_cloud_run_sensor
