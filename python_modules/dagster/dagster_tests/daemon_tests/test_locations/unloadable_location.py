from dagster import (
    AssetIn,
    DailyPartitionsDefinition,
    Definitions,
    TimeWindowPartitionMapping,
    asset,
)


@asset(
    partitions_def=DailyPartitionsDefinition("2023-01-01"),
    ins={
        "error_def_asset": AssetIn(
            partition_mapping=TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)
        )
    },
)
def error_def_asset():  # missing error_def_asset param
    return 1


defs = Definitions([error_def_asset])
