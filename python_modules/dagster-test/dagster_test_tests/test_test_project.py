from dagster_test.test_project import (
    ReOriginatedExternalPipelineForTest,
    get_test_project_external_pipeline,
)


def test_reoriginated_external_pipeline():
    external_pipeline = get_test_project_external_pipeline("demo_pipeline_celery")
    reoriginated_pipeline = ReOriginatedExternalPipelineForTest(external_pipeline)

    assert reoriginated_pipeline.get_origin()
    assert reoriginated_pipeline.get_external_origin()
