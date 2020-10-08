from dagster_examples.simple_pyspark.pipelines import simple_pyspark_sfo_weather_pipeline

from dagster import execute_pipeline


def test_simple_pyspark_sfo_weather_pipeline_success():
    pipeline_result = execute_pipeline(simple_pyspark_sfo_weather_pipeline, preset="local")
    assert pipeline_result.success
