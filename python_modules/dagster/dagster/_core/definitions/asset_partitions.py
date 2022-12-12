from typing import Optional

import dagster._check as check
from dagster._core.definitions import AssetsDefinition

from .events import AssetKey
from .partition import PartitionsDefinition
from .partition_key_range import PartitionKeyRange


def get_upstream_partitions_for_partition_range(
    downstream_assets_def: AssetsDefinition,
    upstream_partitions_def: PartitionsDefinition,
    upstream_asset_key: AssetKey,
    downstream_partition_key_range: Optional[PartitionKeyRange],
) -> PartitionKeyRange:
    """Returns the range of partition keys in the upstream asset that include data necessary
    to compute the contents of the given partition key range in the downstream asset.
    """
    if upstream_partitions_def is None:
        check.failed("upstream asset is not partitioned")

    downstream_partition_mapping = downstream_assets_def.infer_partition_mapping(upstream_asset_key)
    downstream_partitions_def = downstream_assets_def.partitions_def
    downstream_partitions_subset = (
        downstream_partitions_def.empty_subset().with_partition_keys(
            downstream_partitions_def.get_partition_keys_in_range(downstream_partition_key_range)
        )
        if downstream_partitions_def and downstream_partition_key_range
        else None
    )
    upstream_partitions_subset = (
        downstream_partition_mapping.get_upstream_partitions_for_partitions(
            downstream_partitions_subset,
            upstream_partitions_def,
        )
    )
    upstream_key_ranges = upstream_partitions_subset.get_partition_key_ranges()
    check.invariant(len(upstream_key_ranges) == 1)
    return upstream_key_ranges[0]


def get_downstream_partitions_for_partition_range(
    downstream_assets_def: AssetsDefinition,
    upstream_assets_def: AssetsDefinition,
    upstream_asset_key: AssetKey,
    upstream_partition_key_range: PartitionKeyRange,
) -> PartitionKeyRange:
    """Returns the range of partition keys in the downstream asset that use the data in the given
    partition key range of the upstream asset.
    """
    if downstream_assets_def.partitions_def is None:
        check.failed("downstream asset is not partitioned")

    if upstream_assets_def.partitions_def is None:
        check.failed("upstream asset is not partitioned")

    downstream_partition_mapping = downstream_assets_def.infer_partition_mapping(upstream_asset_key)
    upstream_partitions_def = upstream_assets_def.partitions_def
    upstream_partitions_subset = upstream_partitions_def.empty_subset().with_partition_keys(
        upstream_partitions_def.get_partition_keys_in_range(upstream_partition_key_range)
    )
    downstream_partitions_subset = (
        downstream_partition_mapping.get_downstream_partitions_for_partitions(
            upstream_partitions_subset,
            downstream_assets_def.partitions_def,
        )
    )
    downstream_key_ranges = downstream_partitions_subset.get_partition_key_ranges()
    check.invariant(len(downstream_key_ranges) == 1)
    return downstream_key_ranges[0]
