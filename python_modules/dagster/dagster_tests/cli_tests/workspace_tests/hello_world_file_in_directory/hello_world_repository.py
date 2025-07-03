import dagster as dg

# type: ignore
from src.jobs import hello_world_job


@dg.repository
def hello_world_repository():
    return [hello_world_job]
