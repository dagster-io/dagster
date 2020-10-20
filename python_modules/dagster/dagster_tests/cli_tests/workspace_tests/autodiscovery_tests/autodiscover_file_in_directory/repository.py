from autodiscover_src.pipelines import hello_world_pipeline
from dagster import repository


@repository
def hello_world_repository():
    return [hello_world_pipeline]
