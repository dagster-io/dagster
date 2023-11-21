from dagster import DailyPartitionsDefinition, asset


@asset(  # partitions def changed to start in June instead of Jan
    partitions_def=DailyPartitionsDefinition("2023-06-01"),
)
def one():
    pass


@asset  # partitions def removed
def two():
    pass
