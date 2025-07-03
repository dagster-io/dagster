import dagster as dg

pacific = dg.DailyPartitionsDefinition(start_date="2020-01-01", timezone="US/Pacific")


@dg.asset(partitions_def=pacific)
def upstream_asset():
    pass
