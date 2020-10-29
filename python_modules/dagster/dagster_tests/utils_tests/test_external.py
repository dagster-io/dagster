from dagster.core.test_utils import create_run_for_test, instance_for_test
from dagster.utils.external import external_pipeline_from_run
from dagster_tests.api_tests.utils import get_foo_pipeline_handle


def test_get_external_pipeline_from_run():
    with instance_for_test() as instance:
        with get_foo_pipeline_handle() as pipeline_handle:
            run = create_run_for_test(
                instance,
                pipeline_name=pipeline_handle.pipeline_name,
                external_pipeline_origin=pipeline_handle.get_external_origin(),
            )

            with external_pipeline_from_run(run) as external_pipeline:
                assert external_pipeline.name == pipeline_handle.pipeline_name
