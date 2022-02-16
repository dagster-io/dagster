from dagster import build_op_context
from docs_snippets.concepts.assets.observations import (
    asset_observation_job,
    metadata_observation_job,
    partitioned_observation_job,
)


def test_jobs_execute():
    jobs = [
        asset_observation_job,
        metadata_observation_job,
    ]

    for job in jobs:
        assert job.execute_in_process().success

    assert partitioned_observation_job.execute_in_process(partition_key="2022-02-15").success
