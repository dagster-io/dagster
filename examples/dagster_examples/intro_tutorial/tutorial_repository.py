from dagster import RepositoryDefinition

from .actual_dag import actual_dag_pipeline
from .config import hello_with_config_pipeline
from .configuration_schemas import configuration_schema_pipeline
from .execution_context import execution_context_pipeline
from .hello_dag import hello_dag_pipeline
from .hello_world import hello_world_pipeline
from .resources_full import resources_pipeline
from .reusing_solids import reusing_solids_pipeline


def define_repository():
    return RepositoryDefinition(
        name='tutorial_repository',
        pipeline_defs=[
            configuration_schema_pipeline,
            hello_world_pipeline,
            hello_dag_pipeline,
            actual_dag_pipeline,
            hello_with_config_pipeline,
            execution_context_pipeline,
            resources_pipeline,
            reusing_solids_pipeline,
        ],
    )
