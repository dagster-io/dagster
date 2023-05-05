# type: ignore

from dagster import repository
from src.jobs import hello_world_job


@repository
def hello_world_repository():
    return [hello_world_job]
