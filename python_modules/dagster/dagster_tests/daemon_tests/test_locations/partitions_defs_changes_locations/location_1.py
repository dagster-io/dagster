from dagster import DailyPartitionsDefinition, asset


@asset(
    partitions_def=DailyPartitionsDefinition("2023-01-01"),
)
def one():
    pass


@asset(
    partitions_def=DailyPartitionsDefinition("2023-01-01"),
)
def two():
    pass
