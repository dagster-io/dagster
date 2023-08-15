from dagster._core.test_utils import instance_for_test
from dagster_test.test_project import (
    ReOriginatedExternalJobForTest,
    get_test_project_workspace_and_external_job,
)


def test_reoriginated_external_job():
    with instance_for_test() as instance:
        with get_test_project_workspace_and_external_job(instance, "demo_job_celery_k8s") as (
            _workspace,
            external_pipeline,
        ):
            reoriginated_pipeline = ReOriginatedExternalJobForTest(external_pipeline)

            assert reoriginated_pipeline.get_python_origin()
            assert reoriginated_pipeline.get_external_origin()
