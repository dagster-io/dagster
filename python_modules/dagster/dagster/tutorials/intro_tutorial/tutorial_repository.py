from dagster import RepositoryDefinition

from .hello_world import define_hello_world_pipeline
from .hello_dag import define_hello_dag_pipeline
from .actual_dag import define_diamond_dag_pipeline
from .part_four import define_configurable_hello_world_pipeline
from .part_five import define_execution_context_pipeline_step_two


def define_repository():
    return RepositoryDefinition(
        name='tutorial_repository',
        pipeline_dict={
            'hello_world_pipeline': define_hello_world_pipeline,
            'hello_dag_pipeline': define_hello_dag_pipeline,
            'actual_dag_pipeline': define_diamond_dag_pipeline,
            'part_four_pipeline': define_configurable_hello_world_pipeline,
            'part_five_pipeline': define_execution_context_pipeline_step_two,
        },
    )
