from dagster import DailyPartitionsDefinition, StaticPartitionsDefinition, asset


@asset(  # partitions def changed to start in June instead of Jan
    partitions_def=DailyPartitionsDefinition("2023-06-01"),
)
def time_partitions_def_changes():
    pass


@asset  # partitions def removed
def partitions_def_removed():
    pass


@asset(  # partition "c" removed
    partitions_def=StaticPartitionsDefinition(["a", "b"]),
)
def static_partition_removed():
    pass
