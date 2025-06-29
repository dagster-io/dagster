from typing import Optional

from dagster import _check as check
from dagster._core.definitions.partitions.subset import PartitionsSubset
from dagster._core.definitions.partitions.utils import CachingDynamicPartitionsLoader
from dagster._core.remote_representation.external_data import AssetNodeSnap
from dagster._core.storage.partition_status_cache import get_partition_subsets
from dagster._core.workspace.context import WorkspaceRequestContext


def regenerate_and_check_partition_subsets(
    context: WorkspaceRequestContext,
    asset_node_snap: AssetNodeSnap,
    dynamic_partitions_loader: Optional[CachingDynamicPartitionsLoader],
) -> tuple[PartitionsSubset[str], PartitionsSubset[str], PartitionsSubset[str]]:
    if not dynamic_partitions_loader:
        check.failed("dynamic_partitions_loader must be provided to get partition keys")

    (
        materialized_partition_subset,
        failed_partition_subset,
        in_progress_subset,
    ) = get_partition_subsets(
        context.instance,
        context,
        asset_node_snap.asset_key,
        dynamic_partitions_loader,
        (
            asset_node_snap.partitions.get_partitions_definition()
            if asset_node_snap.partitions
            else None
        ),
    )

    if (
        materialized_partition_subset is None
        or failed_partition_subset is None
        or in_progress_subset is None
    ):
        check.failed("Expected partitions subset for a partitioned asset")

    return materialized_partition_subset, failed_partition_subset, in_progress_subset
