from dagster import RepositoryDefinition

from .pipelines import download_gbfs_files


def gbfs_repository():
    return RepositoryDefinition('gbfs_repository', pipeline_defs=[download_gbfs_files])
