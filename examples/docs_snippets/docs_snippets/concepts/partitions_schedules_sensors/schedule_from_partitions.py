"""isort:skip_file"""

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

from .static_partitioned_job import continent_job
# start_static_partition

@schedule(cron_schedule="0 0 * * *", job=continent_job)
def continent_schedule():
    

# end_static_partition