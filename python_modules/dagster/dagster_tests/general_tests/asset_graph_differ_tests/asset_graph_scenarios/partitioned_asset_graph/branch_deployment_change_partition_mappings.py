import dagster as dg

daily_partitions_def = dg.DailyPartitionsDefinition(start_date="2024-02-01")
static_partitions_def = dg.StaticPartitionsDefinition(["apple", "orange", "banana"])
multi_partitions_def = dg.MultiPartitionsDefinition(
    {"date": daily_partitions_def, "fruits": static_partitions_def}
)


@dg.asset(partitions_def=daily_partitions_def)
def daily_upstream():
    return 1


@dg.asset(
    partitions_def=daily_partitions_def,
    ins={
        "daily_upstream": dg.AssetIn(
            partition_mapping=dg.TimeWindowPartitionMapping(start_offset=-4)
        )
    },  # change the time window partition mapping
)
def daily_downstream(daily_upstream):
    return daily_upstream + 1


@dg.asset(partitions_def=static_partitions_def)
def static_upstream():
    return 1


@dg.asset(
    partitions_def=static_partitions_def,
    ins={
        "static_upstream": dg.AssetIn(
            partition_mapping=dg.StaticPartitionMapping(
                {"apple": "banana", "orange": "apple", "banana": "orange"}
            )
        )
    },  # change the static partition mapping
)
def static_downstream(static_upstream):
    return static_upstream + 1


@dg.asset(partitions_def=multi_partitions_def)
def multi_partitioned_upstream():
    return 1


@dg.asset(
    partitions_def=multi_partitions_def,
    ins={
        "multi_partitioned_upstream": dg.AssetIn(
            partition_mapping=dg.MultiPartitionMapping(
                {
                    "date": dg.DimensionPartitionMapping(
                        "daily", dg.TimeWindowPartitionMapping(start_offset=-2)
                    ),
                    "fruits": dg.DimensionPartitionMapping(
                        "fruits",
                        dg.StaticPartitionMapping(
                            {"apple": "banana", "orange": "apple", "banana": "orange"}
                        ),
                    ),
                }
            )
        )
    },
)
def multi_partitioned_downstream(multi_partitioned_upstream):
    return multi_partitioned_upstream + 1


defs = dg.Definitions(
    assets=[
        daily_upstream,
        daily_downstream,
        static_upstream,
        static_downstream,
        multi_partitioned_upstream,
        multi_partitioned_downstream,
    ]
)
