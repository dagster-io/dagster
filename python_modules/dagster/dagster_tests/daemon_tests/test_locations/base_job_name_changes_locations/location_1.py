import dagster as dg


@dg.asset(
    partitions_def=dg.HourlyPartitionsDefinition("2023-01-01-00:00"),
)
def hourly_asset():  # Exists in __ASSET_JOB_0
    pass


@dg.asset(partitions_def=dg.WeeklyPartitionsDefinition("2023-01-05"))
def weekly_asset():  # Exists in __ASSET_JOB_1
    pass
