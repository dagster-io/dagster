# type: ignore

from autodiscover_src.jobs import hello_world_job
from dagster import repository


@repository
def hello_world_repository():
    return [hello_world_job]
