from docs_snippets.guides.build.partitions_backfills.static_partitioned_job import (
    continent_job,
)


def test_continent_job():
    assert continent_job.execute_in_process(partition_key="Asia").success
