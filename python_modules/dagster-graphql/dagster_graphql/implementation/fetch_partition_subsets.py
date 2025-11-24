import asyncio
from typing import Optional

from dagster._core.definitions.asset_health.asset_materialization_health import (
    AssetMaterializationHealthState,
)
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.partitions.subset import PartitionsSubset
from dagster._core.instance.types import CachingDynamicPartitionsLoader
from dagster._core.remote_representation.external_data import AssetNodeSnap
from dagster._core.storage.partition_status_cache import get_partition_subsets
from dagster._core.workspace.context import BaseWorkspaceRequestContext


async def _gen_asset_health_for_partition_subsets(
    context: BaseWorkspaceRequestContext,
    asset_key: AssetKey,
) -> Optional[AssetMaterializationHealthState]:
    if not context.read_partition_subsets_from_asset_health():
        return None

    return await AssetMaterializationHealthState.gen(context, asset_key)


async def regenerate_and_check_partition_subsets(
    context: BaseWorkspaceRequestContext,
    asset_node_snap: AssetNodeSnap,
    dynamic_partitions_loader: CachingDynamicPartitionsLoader,
) -> tuple[
    Optional[PartitionsSubset[str]],
    Optional[PartitionsSubset[str]],
    Optional[PartitionsSubset[str]],
]:
    (
        asset_health_state,
        (materialized_partition_subset, failed_partition_subset, in_progress_subset),
    ) = await asyncio.gather(
        _gen_asset_health_for_partition_subsets(context, asset_node_snap.asset_key),
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

    if asset_health_state:
        # prefer sourcing materialized and failed subsets from the health object if possible
        materialized_partition_subset = (
            asset_health_state.materialized_subset.subset_value
            if asset_health_state.materialized_subset.is_partitioned
            else None
        )
        failed_partition_subset = (
            asset_health_state.failed_subset.subset_value
            if asset_health_state.failed_subset.is_partitioned
            else None
        )

    return (
        materialized_partition_subset,
        failed_partition_subset,
        in_progress_subset,
    )
