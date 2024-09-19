# ruff: isort: skip_file

from docs_snippets.concepts.partitions_schedules_sensors.partitioned_job import (
    partitioned_op_job,
)


# start
def test_partitioned_op_job():
    assert partitioned_op_job.execute_in_process(partition_key="2020-01-01").success


# end
