from dagster import repository

from .pipelines import event_ingest_pipeline


@repository
def event_pipeline_demo_repo():
    return [event_ingest_pipeline]
