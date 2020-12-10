import sys
import warnings

from dagster import repository


def get_event_pipelines():
    from dagster_examples.event_pipeline_demo.pipelines import event_ingest_pipeline

    return [event_ingest_pipeline]


def get_pyspark_pipelines():
    from dagster_examples.simple_pyspark.pipelines import simple_pyspark_sfo_weather_pipeline

    return [simple_pyspark_sfo_weather_pipeline]


def get_lakehouse_pipelines():
    from dagster_examples.simple_lakehouse.pipelines import simple_lakehouse_pipeline

    return [simple_lakehouse_pipeline]


def get_bay_bikes_pipelines():
    if sys.version_info >= (3, 9):
        return []
    try:
        import tensorflow as _
        from dagster_examples.bay_bikes.pipelines import (
            daily_weather_pipeline,
            generate_training_set_and_train_model,
        )

        return [generate_training_set_and_train_model, daily_weather_pipeline]
    except ImportError:
        warnings.warn("tensorflow not installed, skipping bay bikes pipeline")
        return []


@repository
def legacy_examples():
    return (
        get_bay_bikes_pipelines()
        + get_event_pipelines()
        + get_pyspark_pipelines()
        + get_lakehouse_pipelines()
    )
