from dagster import RepositoryDefinition

from .pipelines import (
    define_airline_demo_download_pipeline,
    define_airline_demo_ingest_pipeline,
    define_airline_demo_warehouse_pipeline,
)


def define_repo():
    return RepositoryDefinition(
        name='airline_demo_repo',
        pipeline_dict={
            'airline_demo_download_pipeline': define_airline_demo_download_pipeline,
            'airline_demo_ingest_pipeline': define_airline_demo_ingest_pipeline,
            'airline_demo_warehouse_pipeline': define_airline_demo_warehouse_pipeline,
        },
    )
