from docs_snippets_crag.concepts.partitions_schedules_sensors.partitioned_job import (
    do_stuff_partitioned,
)
from docs_snippets_crag.concepts.partitions_schedules_sensors.schedule_from_partitions import (
    do_stuff_partitioned_schedule,
)


def test_schedule_from_partitions():
    assert do_stuff_partitioned_schedule.pipeline_name == do_stuff_partitioned.name
