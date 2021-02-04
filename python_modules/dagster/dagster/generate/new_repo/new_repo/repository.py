from dagster import repository

from .pipelines import my_pipeline
from .schedules import my_hourly_schedule
from .sensors import my_sensor


@repository
def my_repository():
    """
    The repository definition for this {{ repo_name }} Dagster repository.

    For hints on building your Dagster repository, see our documentation overview on Repositories:
    https://docs.dagster.io/overview/repositories-workspaces/repositories
    """
    pipelines = [my_pipeline]
    schedules = [my_hourly_schedule]
    sensors = [my_sensor]

    return pipelines + schedules + sensors
