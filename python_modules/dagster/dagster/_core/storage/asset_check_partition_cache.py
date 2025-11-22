import dagster._check as check
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
from dagster._core.definitions.partitions.definition import PartitionsDefinition
from dagster._core.definitions.partitions.subset import PartitionsSubset
from dagster._core.definitions.partitions.subset.serialized import SerializedPartitionsSubset
from dagster._core.instance import DagsterInstance
from dagster._core.storage.asset_check_execution_record import (
    AssetCheckExecutionRecordStatus,
    AssetCheckPartitionStatus,
    AssetCheckPartitionStatusCacheValue,
)
from dagster._core.storage.dagster_run import RunsFilter


def get_asset_check_partition_status(
    instance: DagsterInstance,
    check_key: AssetCheckKey,
    partitions_def: PartitionsDefinition,
) -> AssetCheckPartitionStatus:
    """Get computed partition status by reconciling cached data with current definition and run status.

    This is the main entry point for getting asset check partition status, analogous to
    get_and_update_asset_status_cache_value for regular assets.
    """
    check.inst_param(instance, "instance", DagsterInstance)
    check.inst_param(check_key, "check_key", AssetCheckKey)
    check.inst_param(partitions_def, "partitions_def", PartitionsDefinition)

    cache_value = instance.event_log_storage.get_asset_check_cached_value(check_key)
    current_def_id = partitions_def.get_serializable_unique_identifier()

    if cache_value and cache_value.partitions_def_id == current_def_id:
        planned_subset = cache_value.serialized_planned_subset.deserialize(partitions_def)
        succeeded_subset = cache_value.serialized_succeeded_subset.deserialize(partitions_def)
        failed_subset = cache_value.serialized_failed_subset.deserialize(partitions_def)
        planned_run_mapping = cache_value.planned_partition_run_mapping
        after_storage_id = cache_value.latest_storage_id
    else:
        planned_subset = partitions_def.empty_subset()
        succeeded_subset = partitions_def.empty_subset()
        failed_subset = partitions_def.empty_subset()
        planned_run_mapping = {}
        after_storage_id = None

    # fetch all partition records updated after the last cached event ID, to incrementally update
    # the cached value
    partition_records = instance.event_log_storage.get_asset_check_partition_records(
        check_key, after_event_storage_id=after_storage_id
    )
    if partition_records:
        planned_keys = list(planned_subset.get_partition_keys())
        succeeded_keys = list(succeeded_subset.get_partition_keys())
        failed_keys = list(failed_subset.get_partition_keys())

        for record in partition_records:
            # Remove partition from old status lists
            partition_key = record.partition_key
            if partition_key in planned_keys:
                planned_keys.remove(partition_key)
            if partition_key in succeeded_keys:
                succeeded_keys.remove(partition_key)
            if partition_key in failed_keys:
                failed_keys.remove(partition_key)

            # update status for each partition
            if record.last_execution_status == AssetCheckExecutionRecordStatus.PLANNED:
                planned_keys.append(partition_key)
                if record.last_planned_run_id:
                    planned_run_mapping[partition_key] = record.last_planned_run_id
            elif record.last_execution_status == AssetCheckExecutionRecordStatus.SUCCEEDED:
                succeeded_keys.append(partition_key)
                planned_run_mapping.pop(partition_key, None)
            elif record.last_execution_status == AssetCheckExecutionRecordStatus.FAILED:
                failed_keys.append(partition_key)
                planned_run_mapping.pop(partition_key, None)

        # update the subsets
        planned_subset = partitions_def.subset_with_partition_keys(planned_keys)
        succeeded_subset = partitions_def.subset_with_partition_keys(succeeded_keys)
        failed_subset = partitions_def.subset_with_partition_keys(failed_keys)

        max_storage_id = max(
            (r.last_event_id for r in partition_records),
            default=(cache_value.latest_storage_id if cache_value else 0),
        )
        new_cache_value = AssetCheckPartitionStatusCacheValue(
            latest_storage_id=max_storage_id,
            partitions_def_id=current_def_id,
            serialized_planned_subset=SerializedPartitionsSubset.from_subset(
                planned_subset, partitions_def
            ),
            serialized_succeeded_subset=SerializedPartitionsSubset.from_subset(
                succeeded_subset, partitions_def
            ),
            serialized_failed_subset=SerializedPartitionsSubset.from_subset(
                failed_subset, partitions_def
            ),
            planned_partition_run_mapping=planned_run_mapping,
        )
        instance.event_log_storage.update_asset_check_cached_value(check_key, new_cache_value)

    # fetch run status for all planned partitions to break them down into in_progress, skipped, and failed
    in_progress, skipped, execution_failed = _resolve_planned_partition_statuses(
        instance, planned_subset, planned_run_mapping
    )

    all_subset = partitions_def.subset_with_all_partitions()
    missing_subset = all_subset - (succeeded_subset | failed_subset | planned_subset)

    return AssetCheckPartitionStatus(
        missing=missing_subset,
        succeeded=succeeded_subset,
        failed=failed_subset,
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
