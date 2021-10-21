from docs_snippets.concepts.partitions_schedules_sensors.partitioned_job import (
    do_stuff_partitioned,
)


def test_do_stuff():
    assert do_stuff_partitioned.execute_in_process(partition_key="2021-05-01").success
