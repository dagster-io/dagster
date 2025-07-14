import dagster as dg


@dg.asset(
    partitions_def=dg.DailyPartitionsDefinition("2023-01-01"),
)
def time_partitions_def_changes():
    pass


@dg.asset(
    partitions_def=dg.DailyPartitionsDefinition("2023-01-01"),
)
def partitions_def_removed():
    pass


@dg.asset(
    partitions_def=dg.StaticPartitionsDefinition(["a", "b", "c"]),
)
def static_partition_removed():
    pass
