from multi_type_lakehouse.pipelines import multi_type_lakehouse_pipeline

from dagster import execute_pipeline


def test_multi_type_lakehouse():
    pipeline_result = execute_pipeline(multi_type_lakehouse_pipeline, mode='dev')
    assert pipeline_result.success
