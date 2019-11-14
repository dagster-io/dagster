from dagster import RepositoryDefinition

from .pipelines import monthly_bay_bike_etl_pipeline


def define_repo():
    return RepositoryDefinition(
        name='bay_bikes_demo',
        pipeline_dict={'monthly_bay_bike_etl_pipeline': lambda: monthly_bay_bike_etl_pipeline},
    )
