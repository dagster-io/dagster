from dagster import execute_pipeline
from simple_lakehouse.pipelines import simple_lakehouse_pipeline


def test_simple_lakehouse():
    pipeline_result = execute_pipeline(simple_lakehouse_pipeline)
    assert pipeline_result.success
