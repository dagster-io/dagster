from docs_snippets.concepts.partitions_schedules_sensors.partitioned_job import (
    partitioned_op_job,
)


def test_do_stuff():
    assert partitioned_op_job.execute_in_process(partition_key="2021-05-01").success
