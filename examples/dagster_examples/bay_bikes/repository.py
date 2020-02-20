from dagster import RepositoryDefinition

from .pipelines import (
    extract_daily_weather_data_pipeline,
    generate_training_set_and_train_model,
    monthly_trip_pipeline,
)


def define_repo():
    return RepositoryDefinition(
        name='bay_bikes_demo',
        pipeline_dict={
            'extract_daily_weather_data_pipeline': lambda: extract_daily_weather_data_pipeline,
            'monthly_trip_pipeline': lambda: monthly_trip_pipeline,
            'generate_training_set_and_train_model': lambda: generate_training_set_and_train_model,
        },
    )
