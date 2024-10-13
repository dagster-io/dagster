from dagster import (
    AssetIn,
    DailyPartitionsDefinition,
    Definitions,
    DimensionPartitionMapping,
    MultiPartitionMapping,
    MultiPartitionsDefinition,
    StaticPartitionMapping,
    StaticPartitionsDefinition,
    TimeWindowPartitionMapping,
    asset,
)

daily_partitions_def = DailyPartitionsDefinition(start_date="2024-02-01")
static_partitions_def = StaticPartitionsDefinition(["apple", "orange", "banana"])
multi_partitions_def = MultiPartitionsDefinition(
    {"date": daily_partitions_def, "fruits": static_partitions_def}
)


@asset(partitions_def=daily_partitions_def)
def daily_upstream():
    return 1


@asset(
    partitions_def=daily_partitions_def,
    ins={
        "daily_upstream": AssetIn(partition_mapping=TimeWindowPartitionMapping(start_offset=-4))
    },  # change the time window partition mapping
)
def daily_downstream(daily_upstream):
    return daily_upstream + 1


@asset(partitions_def=static_partitions_def)
def static_upstream():
    return 1


@asset(
    partitions_def=static_partitions_def,
    ins={
        "static_upstream": AssetIn(
            partition_mapping=StaticPartitionMapping(
                {"apple": "banana", "orange": "apple", "banana": "orange"}
            )
        )
    },  # change the static partition mapping
)
def static_downstream(static_upstream):
    return static_upstream + 1


@asset(partitions_def=multi_partitions_def)
def multi_partitioned_upstream():
    return 1


@asset(
    partitions_def=multi_partitions_def,
    ins={
        "multi_partitioned_upstream": AssetIn(
            partition_mapping=MultiPartitionMapping(
                {
                    "date": DimensionPartitionMapping(
                        "daily", TimeWindowPartitionMapping(start_offset=-2)
                    ),
                    "fruits": DimensionPartitionMapping(
                        "fruits",
                        StaticPartitionMapping(
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


defs = Definitions(
    assets=[
        daily_upstream,
        daily_downstream,
        static_upstream,
        static_downstream,
        multi_partitioned_upstream,
        multi_partitioned_downstream,
    ]
)
