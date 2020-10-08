from dagster import repository

from .pipelines import define_simple_pyspark_sfo_weather_pipeline


@repository
def simple_pyspark_repo():
    return {
        "pipelines": {
            "simple_pyspark_sfo_weather_pipeline": define_simple_pyspark_sfo_weather_pipeline
        }
    }
