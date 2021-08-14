from dagster import execute_pipeline, reconstructable
from dagster.core.test_utils import instance_for_test
from docs_snippets_crag.deploying.dask_hello_world import (
    dask_pipeline,
)  # pylint: disable=import-error


def test_local_dask_pipeline():
    with instance_for_test() as instance:
        result = execute_pipeline(
            reconstructable(dask_pipeline),
            mode="local",
            run_config={"execution": {"multiprocess": {}}},
            instance=instance,
        )
        assert result.success
        assert result.result_for_solid("hello_world").output_value() == "Hello, World!"
