from collections import defaultdict
from datetime import timedelta
from typing import Dict, Iterator, List, Optional, Sequence, Set, Tuple

from dagster import (
    AssetCheckKey,
    AssetKey,
    AssetMaterialization,
    DefaultSensorStatus,
    JsonMetadataValue,
    MarkdownMetadataValue,
    RunRequest,
    SensorDefinition,
    SensorEvaluationContext,
    SensorResult,
    TimestampMetadataValue,
    _check as check,
    sensor,
)
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.repository_definition.repository_definition import (
    RepositoryDefinition,
)
from dagster._core.utils import toposort_flatten
from dagster._grpc.client import DEFAULT_SENSOR_GRPC_TIMEOUT
from dagster._record import record
from dagster._serdes import deserialize_value, serialize_value
from dagster._serdes.serdes import whitelist_for_serdes
from dagster._time import datetime_from_timestamp, get_current_datetime, get_current_timestamp

from dagster_airlift.constants import MIGRATED_TAG
from dagster_airlift.core.airflow_instance import AirflowInstance
from dagster_airlift.core.utils import get_dag_id_from_asset, get_task_id_from_asset

MAIN_LOOP_TIMEOUT_SECONDS = DEFAULT_SENSOR_GRPC_TIMEOUT - 20
DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS = 1
START_LOOKBACK_SECONDS = 60  # Lookback one minute in time for the initial setting of the cursor.


@whitelist_for_serdes
@record
class AirflowPollingSensorCursor:
    """A cursor that stores the last effective timestamp and the last polled dag id."""

    end_date_gte: Optional[float] = None
    end_date_lte: Optional[float] = None
    dag_query_offset: Optional[int] = None


def build_airflow_polling_sensor(
    airflow_instance: AirflowInstance,
    minimum_interval_seconds: int = DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS,
) -> SensorDefinition:
    @sensor(
        name="airflow_dag_status_sensor",
        minimum_interval_seconds=minimum_interval_seconds,
        default_status=DefaultSensorStatus.RUNNING,
        # This sensor will only ever execute asset checks and not asset materializations.
        asset_selection=AssetSelection.all_asset_checks(),
    )
    def airflow_dag_sensor(context: SensorEvaluationContext) -> SensorResult:
        """Sensor to report materialization events for each asset as new runs come in."""
        repository_def = check.not_none(context.repository_def)
        try:
            cursor = (
                deserialize_value(context.cursor, AirflowPollingSensorCursor)
                if context.cursor
                else AirflowPollingSensorCursor()
            )
        except Exception as e:
            context.log.info(f"Failed to interpret cursor. Starting from scratch. Error: {e}")
            cursor = AirflowPollingSensorCursor()
        current_date = get_current_datetime()
        toposorted_keys = toposorted_asset_keys(repository_def)
        unmigrated_info = get_unmigrated_info(repository_def)
        current_dag_offset = cursor.dag_query_offset or 0
        end_date_gte = (
            cursor.end_date_gte
            or (current_date - timedelta(seconds=START_LOOKBACK_SECONDS)).timestamp()
        )
        end_date_lte = cursor.end_date_lte or current_date.timestamp()
        sensor_iter = materializations_and_requests_from_batch_iter(
            end_date_gte=end_date_gte,
            end_date_lte=end_date_lte,
            offset=current_dag_offset,
            airflow_instance=airflow_instance,
            unmigrated_info=unmigrated_info,
        )
        all_materializations: List[Tuple[float, AssetMaterialization]] = []
        all_check_keys: Set[AssetCheckKey] = set()
        latest_offset = current_dag_offset
        while get_current_datetime() - current_date < timedelta(seconds=MAIN_LOOP_TIMEOUT_SECONDS):
            batch_result = next(sensor_iter, None)
            if batch_result is None:
                break
            all_materializations.extend(batch_result.materializations_and_timestamps)

            for asset_key in batch_result.all_asset_keys_materialized:
                all_check_keys.update(unmigrated_info.checks_per_key[asset_key])
            latest_offset = batch_result.idx

        # Sort materializations by end date and toposort order
        sorted_mats = sorted(
            all_materializations, key=lambda x: (x[0], toposorted_keys.index(x[1].asset_key))
        )
        if batch_result is not None:
            new_cursor = AirflowPollingSensorCursor(
                end_date_gte=end_date_gte,
                end_date_lte=end_date_lte,
                dag_query_offset=latest_offset + 1,
            )
        else:
            # We have completed iteration for this range
            new_cursor = AirflowPollingSensorCursor(
                end_date_gte=end_date_lte,
                end_date_lte=None,
                dag_query_offset=0,
            )
        context.update_cursor(serialize_value(new_cursor))
        return SensorResult(
            asset_events=[sorted_mat[1] for sorted_mat in sorted_mats],
            run_requests=[RunRequest(asset_check_keys=list(all_check_keys))]
            if all_check_keys
            else None,
        )

    return airflow_dag_sensor


@record
class PeeredDagAssetInfo:
    dag_asset_key: AssetKey
    task_asset_keys: Set[Tuple[str, AssetKey]]

    @property
    def task_ids(self) -> Sequence[str]:
        return [task_id for task_id, _ in self.task_asset_keys]

    def asset_keys_for_task(self, task_id: str) -> Sequence[AssetKey]:
        return [asset_key for task_id_, asset_key in self.task_asset_keys if task_id_ == task_id]


@record
class UnmigratedInfo:
    asset_info_by_dag_id: Dict[str, PeeredDagAssetInfo]
    checks_per_key: Dict[AssetKey, Set[AssetCheckKey]]

    @property
    def dag_ids(self) -> Sequence[str]:
        return list(self.asset_info_by_dag_id.keys())


def get_unmigrated_info(
    repository_def: RepositoryDefinition,
) -> UnmigratedInfo:
    """For each dag, retrieve the list of asset keys which correspond, and are unmigrated.
    The key representing the "peered" dag will always be retrieved, but assets whose tasks are marked as "migrated" will not.
    """
    # First, we need to retrieve the upstreams for each asset key
    key_per_dag: Dict[str, AssetKey] = {}
    task_keys_per_dag = defaultdict(set)
    checks_per_key = defaultdict(set)

    for assets_def in repository_def.assets_defs_by_key.values():
        # We could be more specific about the checks here to ensure that there's only one asset key
        # specifying the dag, and that all others have a task id.
        dag_id = get_dag_id_from_asset(assets_def)
        task_id = get_task_id_from_asset(assets_def)
        if dag_id is None:
            continue
        if task_id is None:
            key_per_dag[dag_id] = (
                assets_def.key
            )  # There should only be one key in the case of a "dag" asset
        else:
            migration_state = {spec.tags.get(MIGRATED_TAG) for spec in assets_def.specs}
            check.invariant(
                len(migration_state) == 1,
                "Migration state should match across all specs for a given asset",
            )
            if migration_state.pop() == "True":
                continue

            task_keys_per_dag[dag_id].update((task_id, spec.key) for spec in assets_def.specs)

    for asset_check_key in repository_def.asset_checks_defs_by_key.keys():
        checks_per_key[asset_check_key.asset_key].add(asset_check_key)

    per_dag_asset_info = {
        dag_id: PeeredDagAssetInfo(dag_asset_key=key, task_asset_keys=task_keys_per_dag[dag_id])
        for dag_id, key in key_per_dag.items()
    }
    return UnmigratedInfo(asset_info_by_dag_id=per_dag_asset_info, checks_per_key=checks_per_key)


def toposorted_asset_keys(
    repository_def: RepositoryDefinition,
) -> Sequence[AssetKey]:
    asset_dep_graph = defaultdict(set)  # upstreams
    for assets_def in repository_def.assets_defs_by_key.values():
        for spec in assets_def.specs:
            asset_dep_graph[spec.key].update(dep.asset_key for dep in spec.deps)

    return toposort_flatten(asset_dep_graph)


@record
class BatchResult:
    idx: int
    materializations_and_timestamps: List[Tuple[float, AssetMaterialization]]
    all_asset_keys_materialized: Set[AssetKey]


def materializations_and_requests_from_batch_iter(
    end_date_gte: float,
    end_date_lte: float,
    offset: int,
    airflow_instance: AirflowInstance,
    unmigrated_info: UnmigratedInfo,
) -> Iterator[Optional[BatchResult]]:
    runs = airflow_instance.get_dag_runs_batch(
        dag_ids=unmigrated_info.dag_ids,
        end_date_gte=datetime_from_timestamp(end_date_gte),
        end_date_lte=datetime_from_timestamp(end_date_lte),
        offset=offset,
    )
    for i, dag_run in enumerate(runs):
        peered_dag_asset_info = unmigrated_info.asset_info_by_dag_id[dag_run.dag_id]
        materializations_for_run = []
        all_asset_keys_materialized = set()
        metadata = {
            "Airflow Run ID": dag_run.run_id,
            "Run Metadata (raw)": JsonMetadataValue(dag_run.metadata),
            "Run Type": dag_run.run_type,
            "Airflow Config": JsonMetadataValue(dag_run.config),
            "Creation Timestamp": TimestampMetadataValue(get_current_timestamp()),
        }
        # Add dag materialization
        dag_metadata = {
            **metadata,
            "Run Details": MarkdownMetadataValue(f"[View Run]({dag_run.url})"),
            "Start Date": TimestampMetadataValue(dag_run.start_date),
            "End Date": TimestampMetadataValue(dag_run.end_date),
        }
        materializations_for_run.append(
            (
                dag_run.end_date,
                AssetMaterialization(
                    asset_key=unmigrated_info.asset_info_by_dag_id[dag_run.dag_id].dag_asset_key,
                    description=dag_run.note,
                    metadata=dag_metadata,
                ),
            )
        )
        all_asset_keys_materialized.add(peered_dag_asset_info.dag_asset_key)
        for task_run in airflow_instance.get_task_instance_batch(
            run_id=dag_run.run_id,
            dag_id=dag_run.dag_id,
            task_ids=peered_dag_asset_info.task_ids,
            states=["success"],
        ):
            asset_keys = peered_dag_asset_info.asset_keys_for_task(task_run.task_id)
            task_metadata = {
                **metadata,
                "Run Details": MarkdownMetadataValue(f"[View Run]({task_run.details_url})"),
                "Task Logs": MarkdownMetadataValue(f"[View Logs]({task_run.log_url})"),
                "Start Date": TimestampMetadataValue(task_run.start_date),
                "End Date": TimestampMetadataValue(task_run.end_date),
            }
            for asset_key in asset_keys:
                materializations_for_run.append(
                    (
                        task_run.end_date,
                        AssetMaterialization(
                            asset_key=asset_key,
                            description=task_run.note,
                            metadata=task_metadata,
                        ),
                    )
                )
                all_asset_keys_materialized.add(asset_key)
        yield (
            BatchResult(
                idx=i + offset,
                materializations_and_timestamps=materializations_for_run,
                all_asset_keys_materialized=all_asset_keys_materialized,
            )
            if materializations_for_run
            else None
        )
