from dagster.core.test_utils import instance_for_test
from docs_snippets.guides.dagster.versioning_memoization import memoization_enabled_job


def test_memoization_enabled_job():
    with instance_for_test() as instance:
        result = memoization_enabled_job.the_job.execute_in_process(instance=instance)
        assert result.success
