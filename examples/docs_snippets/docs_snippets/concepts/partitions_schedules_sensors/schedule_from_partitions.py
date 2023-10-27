# ruff: isort: skip_file

from .partitioned_job import my_partitioned_config

# start_marker
from dagster import build_schedule_from_partitioned_job, job


@job(config=my_partitioned_config)
def do_stuff_partitioned():
    ...


do_stuff_partitioned_schedule = build_schedule_from_partitioned_job(
    do_stuff_partitioned,
)

# end_marker


# start_partitioned_asset_schedule
from dagster import (
    asset,
    build_schedule_from_partitioned_job,
    define_asset_job,
    HourlyPartitionsDefinition,
)


@asset(partitions_def=HourlyPartitionsDefinition(start_date="2020-01-01-00:00"))
def hourly_asset():
    ...


partitioned_asset_job = define_asset_job("partitioned_job", selection=[hourly_asset])


asset_partitioned_schedule = build_schedule_from_partitioned_job(
    partitioned_asset_job,
)

# end_partitioned_asset_schedule


from .static_partitioned_job import continent_job, CONTINENTS

# start_static_partition
from dagster import schedule, RunRequest


@schedule(cron_schedule="0 0 * * *", job=continent_job)
def continent_schedule():
    for c in CONTINENTS:
        yield RunRequest(run_key=c, partition_key=c)


# end_static_partition

# start_single_partition


@schedule(cron_schedule="0 0 * * *", job=continent_job)
def antarctica_schedule():
    return RunRequest(partition_key="Antarctica")


# end_single_partition
