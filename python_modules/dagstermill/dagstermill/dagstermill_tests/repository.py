from dagster import (RepositoryDefinition)
from dagstermill.dagstermill_tests.test_basic_dagstermill_solids import (
    define_test_notebook_dag_pipeline, define_hello_world_config_pipeline, define_add_pipeline
)


def define_example_repository():
    return RepositoryDefinition(
        name='notebook_repo',
        pipeline_dict={
            'test_notebook_dag': define_test_notebook_dag_pipeline,
            'test_config_dag': define_hello_world_config_pipeline,
            'test_add_pipeline': define_add_pipeline
        }
    )
