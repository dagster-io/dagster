from dagster import RepositoryDefinition

from .pipelines import event_ingest_pipeline


def define_repo():
    return RepositoryDefinition(
        name='event_pipeline_demo_repo', pipeline_defs=[event_ingest_pipeline]
    )
