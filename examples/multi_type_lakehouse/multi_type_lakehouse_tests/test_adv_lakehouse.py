from dagster import execute_pipeline
from multi_type_lakehouse.pipelines import multi_type_lakehouse_pipeline


def test_multi_type_lakehouse():
    pipeline_result = execute_pipeline(multi_type_lakehouse_pipeline)
    assert pipeline_result.success
