import dagster as dg


@dg.asset(
    partitions_def=dg.DailyPartitionsDefinition("2023-01-01"),
    ins={
        "error_def_asset": dg.AssetIn(
            partition_mapping=dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)
        )
    },
)
def error_def_asset():  # missing error_def_asset param
    return 1


defs = dg.Definitions([error_def_asset])
