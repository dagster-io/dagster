from dagster import RepositoryDefinition

from dagster_pandas.examples import define_papermill_pandas_hello_world_pipeline
from dagster_pandas.examples.pandas_hello_world.pipeline import define_pandas_hello_world_pipeline


def define_repo(repo_config):
    return RepositoryDefinition(
        name='pandas_hello_world_repo',
        pipeline_dict={
            'pandas_hello_world': define_pandas_hello_world_pipeline,
            'papermill_pandas_hello_world_pipeline': define_papermill_pandas_hello_world_pipeline,
        },
        repo_config=repo_config,
    )
