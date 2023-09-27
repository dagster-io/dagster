from dagster import (
    AssetDep,
    DailyPartitionsDefinition,
    TimeWindowPartitionMapping,
    asset,
)

partitions_def = DailyPartitionsDefinition(start_date="2023-01-21")


@asset(partitions_def=partitions_def)
def events():
    ...


@asset(
    partitions_def=partitions_def,
    deps=[
        AssetDep(
            events,
            partition_mapping=TimeWindowPartitionMapping(
                start_offset=-1, end_offset=-1
            ),
        )
    ],
)
def yesterday_event_stats():
    ...
