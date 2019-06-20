from dagster import RepositoryDefinition

from .pipelines import event_ingest_pipeline


def define_repo():
    return RepositoryDefinition(
        name='event_pipeline_demo_repo',
        pipeline_dict={'event_ingest_pipeline': event_ingest_pipeline},
    )
