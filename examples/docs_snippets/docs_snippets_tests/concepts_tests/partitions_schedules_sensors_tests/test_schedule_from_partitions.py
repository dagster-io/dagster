from docs_snippets.concepts.partitions_schedules_sensors.partitioned_job import (
    do_stuff_partitioned,
)
from docs_snippets.concepts.partitions_schedules_sensors.schedule_from_partitions import (
    do_stuff_partitioned_schedule,
)


def test_build_schedule_from_partitioned_job():
    assert do_stuff_partitioned_schedule.job_name == do_stuff_partitioned.name
