from dagster.core.execution.api import ExecutionSelector
from dagster.core.definitions import create_environment_schema
from dagster_graphql.schema.config_types import to_dauphin_config_type
from dagster_graphql.schema.runtime_types import to_dauphin_runtime_type

from .either import EitherError, EitherValue
from .fetch_pipelines import _pipeline_or_error_from_container


def _config_type_or_error(graphene_info, dauphin_pipeline, config_type_name):
    pipeline = dauphin_pipeline.get_dagster_pipeline()
    environment_schema = create_environment_schema(pipeline)
    if not environment_schema.has_config_type(config_type_name):
        return EitherError(
            graphene_info.schema.type_named('ConfigTypeNotFoundError')(
                pipeline=pipeline, config_type_name=config_type_name
            )
        )
    else:
        dauphin_config_type = to_dauphin_config_type(
            environment_schema.config_type_named(config_type_name)
        )
        return EitherValue(dauphin_config_type)


def get_config_type(graphene_info, pipeline_name, type_name):
    pipeline_or_error = _pipeline_or_error_from_container(
        graphene_info, ExecutionSelector(pipeline_name)
    )

    return pipeline_or_error.chain(
        lambda pipeline: _config_type_or_error(graphene_info, pipeline, type_name)
    ).value()


def _runtime_type_or_error(graphene_info, dauphin_pipeline, runtime_type_name):
    pipeline = dauphin_pipeline.get_dagster_pipeline()
    if not pipeline.has_runtime_type(runtime_type_name):
        return EitherError(
            graphene_info.schema.type_named('RuntimeTypeNotFoundError')(
                pipeline=pipeline, runtime_type_name=runtime_type_name
            )
        )
    else:
        dauphin_runtime_type = to_dauphin_runtime_type(
            pipeline.runtime_type_named(runtime_type_name)
        )
        return EitherValue(dauphin_runtime_type)


def get_runtime_type(graphene_info, pipeline_name, type_name):
    pipeline_or_error = _pipeline_or_error_from_container(
        graphene_info, ExecutionSelector(pipeline_name)
    )

    return pipeline_or_error.chain(
        lambda pipeline: _runtime_type_or_error(graphene_info, pipeline, type_name)
    ).value()
