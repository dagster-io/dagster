# isort: skip_file

from docs_snippets.concepts.partitions_schedules_sensors.partitioned_job import (
    do_stuff_partitioned,
)


# start
def test_do_stuff_partitioned():
    assert do_stuff_partitioned.execute_in_process(partition_key="2020-01-01").success


# end
