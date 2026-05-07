from docs_snippets.guides.build.partitions_backfills.partitioned_job import (
    partitioned_op_job,
)
from docs_snippets.guides.build.partitions_backfills.schedule_from_partitions import (
    partitioned_op_schedule,
)


def test_build_schedule_from_partitioned_job():
    assert partitioned_op_schedule.job_name == partitioned_op_job.name
