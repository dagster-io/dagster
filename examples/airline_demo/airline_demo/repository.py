from dagster import repository

from .pipelines import define_airline_demo_ingest_pipeline, define_airline_demo_warehouse_pipeline


@repository
def airline_demo_repo():
    return {
        "pipelines": {
            "airline_demo_ingest_pipeline": define_airline_demo_ingest_pipeline,
            "airline_demo_warehouse_pipeline": define_airline_demo_warehouse_pipeline,
        }
    }
