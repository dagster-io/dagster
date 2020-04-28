from dagster import RepositoryDefinition

from .pipelines import define_simple_pyspark_sfo_weather_pipeline


def define_repo():
    return RepositoryDefinition(
        name='simple_pyspark_repo',
        pipeline_dict={
            'simple_pyspark_sfo_weather_pipeline': define_simple_pyspark_sfo_weather_pipeline
        },
    )
