import dagster as dg
from autodiscover_src.jobs import hello_world_job  # type: ignore


@dg.repository
def hello_world_repository():
    return [hello_world_job]
