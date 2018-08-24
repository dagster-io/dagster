from dagster import (RepositoryDefinition)
from dagster.dagster_examples.pandas_hello_world.pipeline import define_success_pipeline


def define_example_repository():
    return RepositoryDefinition(
        name='example_repo',
        pipeline_dict={'pandas_hello_world': define_success_pipeline},
    )
