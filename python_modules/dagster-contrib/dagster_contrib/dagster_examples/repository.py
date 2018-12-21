from dagster import (RepositoryDefinition)
from dagster_contrib.dagster_examples.pandas_hello_world.pipeline import define_success_pipeline, define_failure_pipeline


def define_example_repository():
    return RepositoryDefinition(
        name='example_repo',
        pipeline_dict={
            'pandas_hello_world': define_success_pipeline,
            'pandas_hello_world_fails': define_failure_pipeline
        },
    )
