from dagster_pandas.examples import papermill_pandas_hello_world_pipeline
from dagster_pandas.examples.pandas_hello_world.pipeline import pandas_hello_world

from dagster import RepositoryDefinition


def define_repo():
    return RepositoryDefinition(
        name='pandas_hello_world_repo',
        pipeline_defs=[pandas_hello_world, papermill_pandas_hello_world_pipeline],
    )
