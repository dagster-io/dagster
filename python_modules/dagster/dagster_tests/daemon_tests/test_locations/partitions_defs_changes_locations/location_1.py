from dagster import asset
from dagster._core.definitions.partitions.definition import (
    DailyPartitionsDefinition,
    StaticPartitionsDefinition,
)


@asset(
    partitions_def=DailyPartitionsDefinition("2023-01-01"),
)
def time_partitions_def_changes():
    pass


@asset(
    partitions_def=DailyPartitionsDefinition("2023-01-01"),
)
def partitions_def_removed():
    pass


@asset(
    partitions_def=StaticPartitionsDefinition(["a", "b", "c"]),
)
def static_partition_removed():
    pass
