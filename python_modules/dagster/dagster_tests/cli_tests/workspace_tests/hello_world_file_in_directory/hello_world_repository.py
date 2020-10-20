from dagster import repository
from src.pipelines import hello_world_pipeline


@repository
def hello_world_repository():
    return [hello_world_pipeline]
