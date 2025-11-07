import asyncio
from typing import Optional

from dagster._core.definitions.partitions.subset import PartitionsSubset
from dagster._core.instance.types import CachingDynamicPartitionsLoader
from dagster._core.remote_representation.external_data import AssetNodeSnap
from dagster._core.storage.partition_status_cache import get_partition_subsets
from dagster._core.workspace.context import WorkspaceRequestContext


async def regenerate_and_check_partition_subsets(
    context: WorkspaceRequestContext,
    asset_node_snap: AssetNodeSnap,
    dynamic_partitions_loader: CachingDynamicPartitionsLoader,
) -> tuple[
    Optional[PartitionsSubset[str]],
    Optional[PartitionsSubset[str]],
    Optional[PartitionsSubset[str]],
]:
    (
        (materialized_partition_subset, failed_partition_subset, in_progress_subset),
    ) = await asyncio.gather(
        get_partition_subsets(
            context.instance,
            context,
            asset_node_snap.asset_key,
            dynamic_partitions_loader,
            (
                asset_node_snap.partitions.get_partitions_definition()
                if asset_node_snap.partitions
                else None
            ),
        ),
    )

    return (
        materialized_partition_subset,
        failed_partition_subset,
        in_progress_subset,
    )
