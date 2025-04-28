import dagster as dg

daily_partition = dg.DailyPartitionsDefinition(start_date="2024-05-20")


@dg.asset(partitions_def=daily_partition)
def daily_asset(): ...


partitioned_asset_job = dg.define_asset_job("partitioned_job", selection=[daily_asset])

# highlight-start
# This partition will run daily
asset_partitioned_schedule = dg.build_schedule_from_partitioned_job(
    partitioned_asset_job,
)
# highlight-end
