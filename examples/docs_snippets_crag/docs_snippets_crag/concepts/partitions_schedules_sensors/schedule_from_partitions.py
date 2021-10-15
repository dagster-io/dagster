"""isort:skip_file"""
from .partitioned_job import do_stuff_partitioned

# start_marker
from dagster import schedule_from_partitions

do_stuff_partitioned_schedule = schedule_from_partitions(do_stuff_partitioned)

# end_marker
