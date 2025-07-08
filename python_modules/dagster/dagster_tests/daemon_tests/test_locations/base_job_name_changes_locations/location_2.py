import dagster as dg


@dg.asset(
    partitions_def=dg.DailyPartitionsDefinition("2022-12-12"),
)
def daily_asset():  # Exists in __ASSET_JOB_0
    pass


@dg.asset(
    partitions_def=dg.HourlyPartitionsDefinition("2023-01-01-00:00"),
)
def hourly_asset():  # Exists in __ASSET_JOB_1
    pass
