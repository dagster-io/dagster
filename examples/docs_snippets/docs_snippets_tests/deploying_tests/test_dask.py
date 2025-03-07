from dagster._core.test_utils import instance_for_test
from docs_snippets.deploying.dask_hello_world import local_dask_job


def test_local_dask_pipeline():
    with instance_for_test() as instance:
        result = local_dask_job.execute_in_process(
            instance=instance,
        )
        assert result.success
        assert result.output_for_node("hello_world") == "Hello, World!"
