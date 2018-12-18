from dagster import RepositoryDefinition

from part_one import define_hello_world_pipeline
from part_two import define_hello_dag_pipeline
from part_three import define_diamond_dag_pipeline
from part_four import define_configurable_hello_world_pipeline
from part_five import define_execution_context_pipeline_step_two


def define_repository():
    return RepositoryDefinition(
        name='tutorial_repository',
        pipeline_dict={
            'part_one_pipeline': define_hello_world_pipeline,
            'part_two_pipeline': define_hello_dag_pipeline,
            'part_three_pipeline': define_diamond_dag_pipeline,
            'part_four_pipeline': define_configurable_hello_world_pipeline,
            'part_five_pipeline': define_execution_context_pipeline_step_two,
        },
    )
