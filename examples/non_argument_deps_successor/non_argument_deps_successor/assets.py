from dagster import (
    AssetOut,
    DailyPartitionsDefinition,
    TimeWindowPartitionMapping,
    asset,
    multi_asset,
)


# single asset case
@asset
def a_single_asset():
    return None


@asset(upstream_assets={"a_single_asset"})  # annoying string duplication....
def downstream_of_single_asset():
    return None


# multi asset case
@multi_asset(outs={"asset_1": AssetOut(), "asset_2": AssetOut()})
def a_multi_asset():
    return None, None


@asset(upstream_assets={"asset_1", "asset_2"})
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
        a_partitioned_asset.with_partition_mapping(
            partition_mapping=TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)
        )
    },
)
def downstream_of_partitioned_asset():
    return None
