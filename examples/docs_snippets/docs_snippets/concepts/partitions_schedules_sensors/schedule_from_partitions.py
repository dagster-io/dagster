"""isort:skip_file"""
from .partitioned_job import do_stuff_partitioned

# start_marker
from dagster import build_schedule_from_partitioned_job

do_stuff_partitioned_schedule = build_schedule_from_partitioned_job(do_stuff_partitioned)

# end_marker
