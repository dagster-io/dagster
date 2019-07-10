from dagster import RepositoryDefinition

from .simple import gcp_data_platform


def define_repo():
    return RepositoryDefinition(name='gcp_data_platform', pipeline_defs=[gcp_data_platform])
