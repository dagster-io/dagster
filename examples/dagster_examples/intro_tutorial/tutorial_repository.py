from dagster import RepositoryDefinition

from .hello_world import hello_world_pipeline
from .hello_dag import hello_dag_pipeline
from .actual_dag import define_actual_dag_pipeline
from .config import hello_with_config_pipeline
from .execution_context import execution_context_pipeline
from .resources_full import resources_pipeline
from .reusable_solids import reusable_solids_pipeline
from .configuration_schemas import configuration_schema_pipeline


def define_repository():
    return RepositoryDefinition(
        name='tutorial_repository',
        pipeline_dict={
            'configuration_schema_pipeline': configuration_schema_pipeline,
            'hello_world_pipeline': hello_world_pipeline,
            'hello_dag_pipeline': hello_dag_pipeline,
            'actual_dag_pipeline': define_actual_dag_pipeline,
            'hello_with_config_pipeline': hello_with_config_pipeline,
            'execution_context_pipeline': execution_context_pipeline,
            'resources_pipeline': resources_pipeline,
            'reusable_solids_pipeline': reusable_solids_pipeline,
        },
    )
