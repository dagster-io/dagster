# isort: skip_file

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

from .static_partitioned_job import continent_job, CONTINENTS

# start_static_partition
from dagster import schedule


@schedule(cron_schedule="0 0 * * *", job=continent_job)
def continent_schedule():
    for c in CONTINENTS:
        request = continent_job.run_request_for_partition(partition_key=c, run_key=c)
        yield request


# end_static_partition

# start_single_partition


@schedule(cron_schedule="0 0 * * *", job=continent_job)
def antarctica_schedule():
    request = continent_job.run_request_for_partition(
        partition_key="Antarctica", run_key=None
    )
    yield request


# end_single_partition
