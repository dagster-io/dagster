from typing import Optional

import dagster._check as check
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
from dagster._core.definitions.partitions.definition import PartitionsDefinition
from dagster._core.instance import DagsterInstance, DynamicPartitionsStore
from dagster._core.storage.asset_check_execution_record import (
    AssetCheckExecutionRecordStatus,
    AssetCheckPartitionSubsets,
)


def get_asset_check_partition_subsets(
    instance: DagsterInstance,
    check_key: AssetCheckKey,
    partitions_def: PartitionsDefinition,
    dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
) -> AssetCheckPartitionSubsets:
    """Get partition subsets by reconciling historical executions with current definition.

    This is the main entry point for getting asset check partition status, analogous to
    get_and_update_asset_status_cache_value for regular assets.
    """
    check.inst_param(instance, "instance", DagsterInstance)
    check.inst_param(check_key, "check_key", AssetCheckKey)
    check.inst_param(partitions_def, "partitions_def", PartitionsDefinition)

    # Get historical execution data from storage layer
    partition_statuses = instance.event_log_storage.get_asset_check_partition_statuses(check_key)

    # Get current partition keys from definition
    current_partition_keys = set(
        partitions_def.get_partition_keys(
            dynamic_partitions_store=dynamic_partitions_store or instance
        )
    )

    succeeded_keys = []
    failed_keys = []
    inProgress_keys = []
    skipped_keys = []
    executionFailed_keys = []
    missing_keys = []

    for partition_key in current_partition_keys:
        if partition_key in partition_statuses:
            status = partition_statuses[partition_key]
            if status == AssetCheckExecutionRecordStatus.SUCCEEDED:
                succeeded_keys.append(partition_key)
            elif status == AssetCheckExecutionRecordStatus.FAILED:
                failed_keys.append(partition_key)
            elif status == AssetCheckExecutionRecordStatus.PLANNED:
                inProgress_keys.append(partition_key)
            else:
                skipped_keys.append(partition_key)
        else:
            # Partition exists in definition but no historical execution = missing
            missing_keys.append(partition_key)

    return AssetCheckPartitionSubsets(
        missing=partitions_def.subset_with_partition_keys(missing_keys),
        succeeded=partitions_def.subset_with_partition_keys(succeeded_keys),
        failed=partitions_def.subset_with_partition_keys(failed_keys),
        inProgress=partitions_def.subset_with_partition_keys(inProgress_keys),
        skipped=partitions_def.subset_with_partition_keys(skipped_keys),
        executionFailed=partitions_def.subset_with_partition_keys(executionFailed_keys),
    )
