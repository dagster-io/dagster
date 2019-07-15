from dagster import RepositoryDefinition

from .final_pipeline import gcp_pipeline


def define_repo():
    return RepositoryDefinition(name='gcp_pipeline', pipeline_defs=[gcp_pipeline])
