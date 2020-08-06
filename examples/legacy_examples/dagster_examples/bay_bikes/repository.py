from dagster import repository

from .pipelines import daily_weather_pipeline, generate_training_set_and_train_model
from .schedules import define_schedules


@repository
def bay_bikes_demo():
    return {
        "pipelines": {
            "generate_training_set_and_train_model": lambda: generate_training_set_and_train_model,
            "daily_weather_pipeline": lambda: daily_weather_pipeline,
        },
        "schedules": define_schedules(),
    }
