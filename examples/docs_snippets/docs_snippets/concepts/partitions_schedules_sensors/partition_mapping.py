import dagster as dg

partitions_def = dg.DailyPartitionsDefinition(start_date="2023-01-21")


@dg.asset(partitions_def=partitions_def)
def events(): ...


@dg.asset(
    partitions_def=partitions_def,
    ins={
        "events": dg.AssetIn(
            partition_mapping=dg.TimeWindowPartitionMapping(
                start_offset=-1, end_offset=-1
            ),
        )
    },
)
def yesterday_event_stats(events): ...
