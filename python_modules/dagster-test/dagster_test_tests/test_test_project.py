from dagster_test.test_project import (
    ReOriginatedExternalPipelineForTest,
    get_test_project_workspace_and_external_pipeline,
)

from dagster._core.test_utils import instance_for_test


def test_reoriginated_external_pipeline():
    with instance_for_test() as instance:
        with get_test_project_workspace_and_external_pipeline(instance, "demo_pipeline_celery") as (
            _workspace,
            external_pipeline,
        ):
            reoriginated_pipeline = ReOriginatedExternalPipelineForTest(external_pipeline)

            assert reoriginated_pipeline.get_python_origin()
            assert reoriginated_pipeline.get_external_origin()
