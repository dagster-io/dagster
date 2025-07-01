from dagster import asset
from dagster._core.definitions.partitions.definition.static import StaticPartitionsDefinition
from dagster._core.definitions.partitions.definition.time_window_subclasses import (
    DailyPartitionsDefinition,
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
