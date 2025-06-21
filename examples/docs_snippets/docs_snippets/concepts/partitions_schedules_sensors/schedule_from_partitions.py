# ruff: isort: skip_file

from .partitioned_job import partitioned_config

# start_marker
import dagster as dg


@dg.job(config=partitioned_config)
def partitioned_op_job(): ...


partitioned_op_schedule = dg.build_schedule_from_partitioned_job(
    partitioned_op_job,
)

# end_marker


# start_partitioned_asset_schedule
import dagster as dg


daily_partition = dg.DailyPartitionsDefinition(start_date="2024-05-20")


@dg.asset(partitions_def=daily_partition)
def daily_asset(): ...


partitioned_asset_job = dg.define_asset_job("partitioned_job", selection=[daily_asset])


asset_partitioned_schedule = dg.build_schedule_from_partitioned_job(
    partitioned_asset_job,
)

# end_partitioned_asset_schedule


from .static_partitioned_job import continent_job, CONTINENTS

# start_static_partition
import dagster as dg


@dg.schedule(cron_schedule="0 0 * * *", job=continent_job)
def continent_schedule():
    for c in CONTINENTS:
        yield dg.RunRequest(run_key=c, partition_key=c)


# end_static_partition

# start_single_partition


@dg.schedule(cron_schedule="0 0 * * *", job=continent_job)
def antarctica_schedule():
    return dg.RunRequest(partition_key="Antarctica")


# end_single_partition

# start_offset_partition
import dagster as dg

daily_partition_with_offset = dg.DailyPartitionsDefinition(
    start_date="2024-05-20", end_offset=-1
)


# end_offset_partition

# start_partitioned_schedule_with_offset
import dagster as dg

asset_partitioned_schedule = dg.build_schedule_from_partitioned_job(
    partitioned_asset_job, hour_of_day=1, minute_of_hour=30
)

# end_partitioned_schedule_with_offset
