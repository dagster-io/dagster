from dagster import RepositoryDefinition
from dagstermill.dagstermill_tests.test_basic_dagstermill_solids import (
    define_test_notebook_dag_pipeline,
    define_add_pipeline,
    define_hello_world_with_output_pipeline,
    define_hello_world_pipeline,
)


def define_example_repository():
    return RepositoryDefinition(
        name='notebook_repo',
        pipeline_dict={
            'test_notebook_dag': define_test_notebook_dag_pipeline,
            'test_add_pipeline': define_add_pipeline,
            'hello_world_with_output_pipeline': define_hello_world_with_output_pipeline,
            'hello_world_pipeline': define_hello_world_pipeline,
        },
    )
