from dagster import RepositoryDefinition

from .pipelines import download_csv_pipeline


def define_repo():
    return RepositoryDefinition(
        name='bay_bikes_demo',
        pipeline_dict={'download_csv_pipeline': lambda: download_csv_pipeline},
    )
