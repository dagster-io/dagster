import dagster as dg


@dg.asset(  # partitions def changed to start in June instead of Jan
    partitions_def=dg.DailyPartitionsDefinition("2023-06-01"),
)
def time_partitions_def_changes():
    pass


@dg.asset  # partitions def removed
def partitions_def_removed():
    pass


@dg.asset(  # partition "c" removed
    partitions_def=dg.StaticPartitionsDefinition(["a", "b"]),
)
def static_partition_removed():
    pass
