from dagster import RepositoryDefinition

from .pipelines import define_event_ingest_pipeline


def define_repo():
    return RepositoryDefinition(
        name='event_pipeline_demo_repo',
        pipeline_dict={'event_ingest_pipeline': define_event_ingest_pipeline},
    )
