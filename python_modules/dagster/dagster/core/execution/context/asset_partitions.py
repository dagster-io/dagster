from typing import TYPE_CHECKING

from dagster import check
from dagster.core.definitions.dependency import NodeHandle
from dagster.core.definitions.partition import PartitionsDefinition
from dagster.core.definitions.partition_key_range import PartitionKeyRange
from dagster.core.definitions.time_window_partitions import (
    TimeWindow,
    TimeWindowPartitionsDefinition,
)

if TYPE_CHECKING:
    from dagster.core.system_config.objects import ResolvedRunConfig


def asset_partition_key_range_for_output(
    op_handle: NodeHandle, output_name: str, resolved_run_config: "ResolvedRunConfig"
) -> PartitionKeyRange:
    op_config = resolved_run_config.op_config(op_handle)
    if op_config is not None and "assets" in op_config:
        all_output_asset_partitions = op_config["assets"].get("output_partitions")
        if all_output_asset_partitions is not None:
            this_output_asset_partitions = all_output_asset_partitions.get(output_name)
            if this_output_asset_partitions is not None:
                return PartitionKeyRange(
                    this_output_asset_partitions["start"], this_output_asset_partitions["end"]
                )

    check.failed("The output has no asset partitions")


def asset_partitions_time_window(
    partitions_def: PartitionsDefinition, partition_key_range: PartitionKeyRange
) -> TimeWindow:
    """The time window for the partitions of the asset correponding to the given output.

    Raises an error if either of the following are true:
    - The output asset has no partitioning.
    - The output asset is not partitioned with a TimeWindowPartitionsDefinition.
    """
    if not partitions_def:
        raise ValueError(
            "Tried to get asset partitions for an input or output that does not correspond to a "
            "partitioned asset."
        )

    if not isinstance(partitions_def, TimeWindowPartitionsDefinition):
        raise ValueError(
            "Tried to get asset partitions for an input or output that correponds to a partitioned "
            "asset that is not partitioned with a TimeWindowPartitionsDefinition."
        )
    return TimeWindow(
        # mypy thinks partitions_def is <nothing> here because ????
        partitions_def.time_window_for_partition_key(partition_key_range.start).start,  # type: ignore
        partitions_def.time_window_for_partition_key(partition_key_range.end).end,  # type: ignore
    )
