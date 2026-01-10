from collections.abc import Mapping
from typing import Optional

from dagster_shared.record import record
from dagster_shared.serdes import whitelist_for_serdes

from dagster._core.asset_graph_view.serializable_entity_subset import SerializableEntitySubset
from dagster._core.definitions.asset_key import AssetCheckKey
from dagster._core.definitions.partitions.definition.partitions_definition import (
    PartitionsDefinition,
)
from dagster._core.loader import LoadingContext
from dagster._core.storage.asset_check_execution_record import (
    AssetCheckExecutionRecordStatus,
    AssetCheckExecutionResolvedStatus,
    AssetCheckPartitionRecord,
)
from dagster._core.storage.dagster_run import DagsterRunStatus, RunRecord


@whitelist_for_serdes
@record
class AssetCheckStatusCacheValue:
    latest_storage_id: int
    subsets: Mapping[AssetCheckExecutionResolvedStatus, SerializableEntitySubset[AssetCheckKey]]
    in_progress_runs: Mapping[str, SerializableEntitySubset[AssetCheckKey]]

    def compatible_with(self, partitions_def: Optional[PartitionsDefinition]) -> bool:
        subset = next(iter(self.subsets.values()), None)
        if subset is None:
            return True
        return subset.is_compatible_with_partitions_def(partitions_def)

    @classmethod
    def empty(cls) -> "AssetCheckStatusCacheValue":
        return cls(latest_storage_id=0, subsets={}, in_progress_runs={})


def _update_subsets_from_partition_records(
    partition_records: Mapping[str, AssetCheckPartitionRecord],
    key: AssetCheckKey,
    partitions_def: PartitionsDefinition,
    initial_subsets: dict[
        AssetCheckExecutionResolvedStatus, SerializableEntitySubset[AssetCheckKey]
    ],
    initial_in_progress_runs: dict[str, SerializableEntitySubset[AssetCheckKey]],
) -> tuple[
    dict[AssetCheckExecutionResolvedStatus, SerializableEntitySubset[AssetCheckKey]],
    dict[str, SerializableEntitySubset[AssetCheckKey]],
]:
    """Returns a set of updated subsets based on new partition records and the latest materialization storage ids."""
    new_subsets = {
        status: initial_subsets.get(status, SerializableEntitySubset.empty(key, partitions_def))
        for status in AssetCheckExecutionResolvedStatus
    }
    new_in_progress_runs = dict(initial_in_progress_runs)
    empty_subset = SerializableEntitySubset.empty(key, partitions_def)

    for pk, check_record in partition_records.items():
        if pk is None or not partitions_def.has_partition_key(pk):
            continue

        partition_subset = SerializableEntitySubset.from_coercible_value(key, pk, partitions_def)

        if (check_record.last_materialization_storage_id or 0) > check_record.last_storage_id:
            # new materialization, clear the check status
            for status in new_subsets:
                new_subsets[status] = new_subsets[status].compute_difference(partition_subset)

        elif check_record.last_execution_status == AssetCheckExecutionRecordStatus.PLANNED:
            # Add to IN_PROGRESS and track run
            new_subsets[AssetCheckExecutionResolvedStatus.IN_PROGRESS] = new_subsets[
                AssetCheckExecutionResolvedStatus.IN_PROGRESS
            ].compute_union(partition_subset)
            run_id = check_record.last_planned_run_id
            new_in_progress_runs[run_id] = new_in_progress_runs.get(
                run_id, empty_subset
            ).compute_union(partition_subset)

        elif check_record.last_execution_status in (
            AssetCheckExecutionRecordStatus.SUCCEEDED,
            AssetCheckExecutionRecordStatus.FAILED,
        ):
            last_mat_storage_id = check_record.last_materialization_storage_id
            last_target_mat_storage_id = (
                check_record.last_execution_target_materialization_storage_id
            )

            if last_mat_storage_id is None or last_mat_storage_id == last_target_mat_storage_id:
                # Check is current, set appropriate status
                status = (
                    AssetCheckExecutionResolvedStatus.SUCCEEDED
                    if check_record.last_execution_status
                    == AssetCheckExecutionRecordStatus.SUCCEEDED
                    else AssetCheckExecutionResolvedStatus.FAILED
                )
                new_subsets[status] = new_subsets[status].compute_union(partition_subset)
            # else: stale check, partition stays unknown (already cleared)

    return new_subsets, new_in_progress_runs


def _apply_in_progress_resolution(
    loading_context: LoadingContext,
    key: AssetCheckKey,
    partitions_def: PartitionsDefinition,
    subsets: dict[AssetCheckExecutionResolvedStatus, SerializableEntitySubset[AssetCheckKey]],
    in_progress_runs: dict[str, SerializableEntitySubset[AssetCheckKey]],
) -> tuple[
    dict[AssetCheckExecutionResolvedStatus, SerializableEntitySubset[AssetCheckKey]],
    dict[str, SerializableEntitySubset[AssetCheckKey]],
]:
    """Resolve in-progress runs that have completed.

    This checks if any runs tracked in in_progress_runs have finished,
    and moves their partitions to SKIPPED or EXECUTION_FAILED.
    """
    if not in_progress_runs:
        return subsets, in_progress_runs

    delta_skipped, delta_execution_failed, resolved_run_ids = _resolve_in_progress_subsets(
        loading_context, key, partitions_def, in_progress_runs
    )

    new_in_progress_runs = {
        run_id: subset
        for run_id, subset in in_progress_runs.items()
        if run_id not in resolved_run_ids
    }

    new_subsets = dict(subsets)
    new_subsets[AssetCheckExecutionResolvedStatus.IN_PROGRESS] = (
        new_subsets[AssetCheckExecutionResolvedStatus.IN_PROGRESS]
        .compute_difference(delta_skipped)
        .compute_difference(delta_execution_failed)
    )
    new_subsets[AssetCheckExecutionResolvedStatus.SKIPPED] = new_subsets[
        AssetCheckExecutionResolvedStatus.SKIPPED
    ].compute_union(delta_skipped)
    new_subsets[AssetCheckExecutionResolvedStatus.EXECUTION_FAILED] = new_subsets[
        AssetCheckExecutionResolvedStatus.EXECUTION_FAILED
    ].compute_union(delta_execution_failed)

    return new_subsets, new_in_progress_runs


def _resolve_in_progress_subsets(
    loading_context: LoadingContext,
    key: AssetCheckKey,
    partitions_def: PartitionsDefinition,
    in_progress_runs: Mapping[str, SerializableEntitySubset[AssetCheckKey]],
) -> tuple[
    SerializableEntitySubset[AssetCheckKey],
    SerializableEntitySubset[AssetCheckKey],
    set[str],
]:
    """Resolve in-progress runs that have completed.

    Returns:
        Tuple of (delta_skipped, delta_execution_failed, resolved_run_ids)
    """
    run_ids = list(in_progress_runs.keys())
    run_records = RunRecord.blocking_get_many(loading_context, in_progress_runs.keys())

    empty_subset = SerializableEntitySubset.empty(key, partitions_def)
    delta_skipped = empty_subset
    delta_execution_failed = empty_subset
    resolved_run_ids: set[str] = set()

    for run_id, run_record in zip(run_ids, run_records):
        if run_record is None or run_record.dagster_run.is_finished:
            resolved_run_ids.add(run_id)
            if run_record and run_record.dagster_run.status == DagsterRunStatus.FAILURE:
                delta_execution_failed = delta_execution_failed.compute_union(
                    in_progress_runs[run_id]
                )
            else:
                delta_skipped = delta_skipped.compute_union(in_progress_runs[run_id])

    return delta_skipped, delta_execution_failed, resolved_run_ids


def get_updated_asset_check_status_cache_value(
    key: AssetCheckKey,
    partitions_def: PartitionsDefinition,
    loading_context: LoadingContext,
) -> AssetCheckStatusCacheValue:
    """Compute an updated cache value for the given asset check using per-partition records.

    This function fetches new check and materialization events, identifies affected partitions,
    and resolves the status for each partition by comparing the latest check execution against
    the latest materialization.
    """
    current_value = None  # TODO: actually store / load this
    if current_value is None or not current_value.compatible_with(partitions_def):
        current_value = AssetCheckStatusCacheValue.empty()

    empty_subset = SerializableEntitySubset.empty(key, partitions_def)

    # Phase 1: Fetch new check records and partitions with new materializations
    check_records = loading_context.instance.event_log_storage.get_asset_check_partition_records(
        key, after_storage_id=current_value.latest_storage_id
    )

    # Phase 2: Update subsets from partition records
    initial_subsets = {
        status: current_value.subsets.get(status, empty_subset)
        for status in AssetCheckExecutionResolvedStatus
    }
    if not check_records:
        # No updates needed, just resolve in-progress runs
        new_subsets, new_in_progress_runs = initial_subsets, dict(current_value.in_progress_runs)
    else:
        # Filter out None partition keys (only handle partitioned assets)
        partition_records: dict[str, AssetCheckPartitionRecord] = {}
        for r in check_records:
            if r.partition_key is not None:
                partition_records[r.partition_key] = r
        new_subsets, new_in_progress_runs = _update_subsets_from_partition_records(
            partition_records,
            key,
            partitions_def,
            initial_subsets,
            dict(current_value.in_progress_runs),
        )

    # Phase 3: Resolve completed in-progress runs
    new_subsets, new_in_progress_runs = _apply_in_progress_resolution(
        loading_context, key, partitions_def, new_subsets, new_in_progress_runs
    )

    # Compute new check cursor
    new_latest_storage_id = max(
        (max(r.last_storage_id, r.last_materialization_storage_id or 0) for r in check_records),
        default=current_value.latest_storage_id,
    )
    return AssetCheckStatusCacheValue(
        latest_storage_id=new_latest_storage_id,
        subsets=new_subsets,
        in_progress_runs=new_in_progress_runs,
    )
