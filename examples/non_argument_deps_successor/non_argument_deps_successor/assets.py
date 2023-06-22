from dagster import (
    AssetOut,
    DailyPartitionsDefinition,
    TimeWindowPartitionMapping,
    asset,
    multi_asset,
)
from dagster._core.definitions.asset_in import AssetIn
from dagster._core.definitions.decorators.asset_decorator import UpstreamAsset


# single asset case
@asset
def a_single_asset():
    return None


@asset(upstream_assets={UpstreamAsset(key="a_single_asset")})  # annoying string duplication....
def downstream_of_single_asset():
    return None


# multi asset case
@multi_asset(outs={"asset_1": AssetOut(), "asset_2": AssetOut()})
def a_multi_asset():
    return None, None


@asset(upstream_assets={UpstreamAsset(key="asset_1"), UpstreamAsset("asset_2")})
def downstream_of_multi_asset():
    return None


# partitioned asset case
partitions_def = DailyPartitionsDefinition(start_date="2023-06-20")


@asset(partitions_def=partitions_def)
def a_partitioned_asset():
    return None


@asset(
    partitions_def=partitions_def,
    upstream_assets={
        UpstreamAsset(
            key="a_partitioned_asset",
            partition_mapping=TimeWindowPartitionMapping(start_offset=-1, end_offset=-1),
        )
    },
)
def downstream_of_partitioned_asset():
    """Theres potentially a bug with this where if i materialize 2023-6-20 of a_partitioned_asset
    the UI shows that 2023-6-21 can't be materialized of this asset since the upstream data is missing, but
    this asset should depend on yesterdays data.... But i see the same behavior in the set of assets below that don't use the new APIs....
    """
    return None


@asset(partitions_def=partitions_def)
def normal_partitioned_asset():
    return None


@asset(
    partitions_def=partitions_def,
    ins={
        "normal_partitioned_asset": AssetIn(
            partition_mapping=TimeWindowPartitionMapping(start_offset=-1, end_offset=-1),
        )
    },
)
def downstream_of_normal_partitioned_asset(normal_partitioned_asset):
    return None
