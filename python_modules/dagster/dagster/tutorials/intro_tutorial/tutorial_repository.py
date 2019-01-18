from dagster import RepositoryDefinition

from .hello_world import define_hello_world_pipeline
from .hello_dag import define_hello_dag_pipeline
from .actual_dag import define_diamond_dag_pipeline
from .config import define_configurable_hello_pipeline
from .execution_context import define_execution_context_pipeline_step_two
from .resources import define_resource_test_pipeline
from .reusable_solids import define_reusable_solids_pipeline
from .multiple_outputs import define_multiple_outputs_step_one_pipeline


def define_repository():
    return RepositoryDefinition(
        name='tutorial_repository',
        pipeline_dict={
            'hello_world_pipeline': define_hello_world_pipeline,
            'hello_dag_pipeline': define_hello_dag_pipeline,
            'actual_dag_pipeline': define_diamond_dag_pipeline,
            'configurable_hello_pipeline': define_configurable_hello_pipeline,
            'execution_context_pipeline': define_execution_context_pipeline_step_two,
            'resource_test_pipeline': define_resource_test_pipeline,
            'multiple_outputs_step_one_pipeline': define_multiple_outputs_step_one_pipeline,
            'reusable_solids_pipeline': define_reusable_solids_pipeline,
        },
    )
