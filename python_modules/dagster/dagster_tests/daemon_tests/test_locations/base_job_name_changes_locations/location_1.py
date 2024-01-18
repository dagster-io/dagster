from dagster import HourlyPartitionsDefinition, WeeklyPartitionsDefinition, asset


@asset(
    partitions_def=HourlyPartitionsDefinition("2023-01-01-00:00"),
)
def hourly_asset():  # Exists in __ASSET_JOB_0
    pass


@asset(partitions_def=WeeklyPartitionsDefinition("2023-01-05"))
def weekly_asset():  # Exists in __ASSET_JOB_1
    pass
