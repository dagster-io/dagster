from dagster import DailyPartitionsDefinition, HourlyPartitionsDefinition, asset


@asset(
    partitions_def=DailyPartitionsDefinition("2022-12-12"),
)
def daily_asset():  # Exists in __ASSET_JOB_0
    pass


@asset(
    partitions_def=HourlyPartitionsDefinition("2023-01-01-00:00"),
)
def hourly_asset():  # Exists in __ASSET_JOB_1
    pass
