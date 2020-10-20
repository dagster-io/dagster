from dagster import execute_pipeline
from dagster_examples.simple_lakehouse.pipelines import simple_lakehouse_pipeline


def test_simple_lakehouse_pipeline():
    pipeline_result = execute_pipeline(simple_lakehouse_pipeline, mode="dev")
    assert pipeline_result.success
