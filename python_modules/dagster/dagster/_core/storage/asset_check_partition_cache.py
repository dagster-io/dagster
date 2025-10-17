from typing import Optional

from dagster._core.asset_graph_view.serializable_entity_subset import SerializableEntitySubset
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
from dagster._core.definitions.partitions.definition import PartitionsDefinition
from dagster._core.definitions.partitions.subset import PartitionsSubset
from dagster._core.instance import DagsterInstance
from dagster._core.loader import LoadingContext
from dagster._core.storage.asset_check_execution_record import (
    AssetCheckExecutionRecord,
    AssetCheckExecutionRecordStatus,
    AssetCheckPartitionStatus,
    AssetCheckPartitionStatusCacheValue,
)
from dagster._core.storage.dagster_run import RunsFilter


def get_updated_asset_check_partition_status(
    loading_context: LoadingContext,
    check_key: AssetCheckKey,
    partitions_def: PartitionsDefinition,
    current_cache_value: Optional[AssetCheckPartitionStatusCacheValue],
) -> AssetCheckPartitionStatusCacheValue:
    """Get computed partition status by reconciling cached data with current definition and run status.

    This is the main entry point for getting asset check partition status, analogous to
    get_and_update_asset_status_cache_value for regular assets.
    """
    instance = loading_context.instance

    # reset the cache value if the partitions definition has changed
    current_def_id = partitions_def.get_serializable_unique_identifier()
    if current_cache_value is None or current_cache_value.partitions_def_id != current_def_id:
        current_cache_value = AssetCheckPartitionStatusCacheValue.from_partitions_def(
            check_key, partitions_def
        )

    # no new check records, exit early
    latest_check_execution_record = AssetCheckExecutionRecord.blocking_get(
        loading_context, check_key
    )
    if (
        latest_check_execution_record
        and latest_check_execution_record.id <= current_cache_value.latest_check_execution_record_id
    ):
        return current_cache_value

    # fetch all partition records updated after the last cached event ID, to incrementally update
    # the cached value
    after_storage_id = current_cache_value.latest_storage_id
    partition_records = instance.event_log_storage.get_asset_check_partition_records(
        check_key, after_event_storage_id=after_storage_id
    )
    # no new data
    if not partition_records:
        return current_cache_value

    newly_planned_keys = set()
    newly_succeeded_keys = set()
    newly_failed_keys = set()
    new_planned_run_mapping = current_cache_value.planned_partition_run_mapping.copy()
    for record in partition_records:
        partition_key = record.partition_key

        # update status for each partition
        if record.last_execution_status == AssetCheckExecutionRecordStatus.PLANNED:
            newly_planned_keys.add(partition_key)
            if record.last_planned_run_id:
                new_planned_run_mapping[partition_key] = record.last_planned_run_id
        elif record.last_execution_status == AssetCheckExecutionRecordStatus.SUCCEEDED:
            newly_succeeded_keys.add(partition_key)
            new_planned_run_mapping.pop(record.partition_key, None)
        elif record.last_execution_status == AssetCheckExecutionRecordStatus.FAILED:
            newly_failed_keys.add(partition_key)
            new_planned_run_mapping.pop(partition_key, None)

    newly_planned_subset = SerializableEntitySubset(
        key=check_key, value=partitions_def.subset_with_partition_keys(newly_planned_keys)
    )
    newly_succeeded_subset = SerializableEntitySubset(
        key=check_key, value=partitions_def.subset_with_partition_keys(newly_succeeded_keys)
    )
    newly_failed_subset = SerializableEntitySubset(
        key=check_key, value=partitions_def.subset_with_partition_keys(newly_failed_keys)
    )

    # update the subsets
    planned_subset = (
        current_cache_value.planned_subset.compute_union(newly_planned_subset)
        .compute_difference(newly_succeeded_subset)
        .compute_difference(newly_failed_subset)
    )
    succeeded_subset = (
        current_cache_value.succeeded_subset.compute_union(newly_succeeded_subset)
        .compute_difference(newly_planned_subset)
        .compute_difference(newly_failed_subset)
    )
    failed_subset = (
        current_cache_value.failed_subset.compute_union(newly_failed_subset)
        .compute_difference(newly_planned_subset)
        .compute_difference(newly_succeeded_subset)
    )

    max_storage_id = max(
        (r.last_event_id for r in partition_records),
        default=(current_cache_value.latest_storage_id),
    )

    return AssetCheckPartitionStatusCacheValue(
        key=check_key,
        latest_storage_id=max_storage_id,
        latest_check_execution_record_id=latest_check_execution_record.id,
        partitions_def_id=current_def_id,
        planned_subset=planned_subset,
        succeeded_subset=succeeded_subset,
        failed_subset=failed_subset,
        planned_partition_run_mapping=new_planned_run_mapping,
    )


async def get_asset_check_partition_status(
    loading_context: LoadingContext,
    check_key: AssetCheckKey,
    partitions_def: PartitionsDefinition,
) -> AssetCheckPartitionStatus:
    cache_value = await AssetCheckPartitionStatusCacheValue.gen(
        loading_context, (check_key, partitions_def)
    ) or AssetCheckPartitionStatusCacheValue.from_partitions_def(check_key, partitions_def)
    in_progress, skipped, execution_failed = _resolve_planned_partition_statuses(
        loading_context.instance,
        cache_value.planned_subset.value,
        cache_value.planned_partition_run_mapping,
    )

    all_subset = partitions_def.subset_with_all_partitions()
    missing_subset = all_subset - (
        cache_value.succeeded_subset.value
        | cache_value.failed_subset.value
        | cache_value.planned_subset.value
    )

    return AssetCheckPartitionStatus(
        missing=missing_subset,
        succeeded=cache_value.succeeded_subset.value,
        failed=cache_value.failed_subset.value,
        in_progress=in_progress,
        skipped=skipped,
        execution_failed=execution_failed,
    )


def _resolve_planned_partition_statuses(
    instance: DagsterInstance,
    planned_subset: PartitionsSubset,
    planned_run_mapping: dict[str, str],
) -> tuple[PartitionsSubset, PartitionsSubset, PartitionsSubset]:
    """Break down planned partitions into in_progress, skipped, and execution_failed based on run status."""
    if planned_subset.is_empty:
        return (
            planned_subset.empty_subset(),
            planned_subset.empty_subset(),
            planned_subset.empty_subset(),
        )

    # Get unique run IDs from the mapping
    run_ids = list(set(planned_run_mapping.values()))

    if not run_ids:
        # No run mapping available, mark all as in_progress
        return planned_subset, planned_subset.empty_subset(), planned_subset.empty_subset()

    # Query run status for all relevant runs
    run_records = instance.get_run_records(RunsFilter(run_ids=run_ids))
    records_by_run_id = {record.dagster_run.run_id: record for record in run_records}

    # Categorize partitions by run status
    in_progress = []
    skipped = []
    execution_failed = []

    for partition_key in planned_subset.get_partition_keys():
        run_id = planned_run_mapping.get(partition_key)
        if not run_id:
            skipped.append(partition_key)
            continue

        run_record = records_by_run_id.get(run_id)
        if not run_record:
            # run deleted
            skipped.append(partition_key)
        elif not run_record.dagster_run.is_finished:
            in_progress.append(partition_key)
        elif run_record.dagster_run.is_failure_or_canceled:
            execution_failed.append(partition_key)
        else:
            # Unknown status, assume in progress
            in_progress.append(partition_key)

    return (
        planned_subset.with_partition_keys(in_progress),
        planned_subset.with_partition_keys(skipped),
        planned_subset.with_partition_keys(execution_failed),
    )
