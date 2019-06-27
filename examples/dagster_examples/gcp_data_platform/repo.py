from dagster import RepositoryDefinition

from .simple import gcp_pipeline


def define_repo():
    return RepositoryDefinition(
        name='gcp_data_platform', pipeline_dict={'gcp_pipeline': gcp_pipeline}
    )
