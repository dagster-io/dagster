from dagster import check

from dagster.core.execution.api import ExecutionSelector
from dagster.core.definitions import create_environment_schema
from dagster_graphql.schema.config_types import to_dauphin_config_type
from dagster_graphql.schema.runtime_types import to_dauphin_runtime_type

from .fetch_pipelines import get_dagster_pipeline_from_selector
from .utils import UserFacingGraphQLError, capture_dauphin_error


@capture_dauphin_error
def get_config_type(graphene_info, pipeline_name, config_type_name, mode):
    check.str_param(pipeline_name, 'pipeline_name')
    check.str_param(config_type_name, 'config_type_name')
    check.opt_str_param(mode, 'mode')

    pipeline = get_dagster_pipeline_from_selector(graphene_info, ExecutionSelector(pipeline_name))
    environment_schema = create_environment_schema(pipeline, mode)
    if not environment_schema.has_config_type(config_type_name):
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('ConfigTypeNotFoundError')(
                pipeline=pipeline, config_type_name=config_type_name
            )
        )

    return to_dauphin_config_type(environment_schema.config_type_named(config_type_name))


@capture_dauphin_error
def get_runtime_type(graphene_info, pipeline_name, type_name):
    pipeline = get_dagster_pipeline_from_selector(graphene_info, ExecutionSelector(pipeline_name))

    if not pipeline.has_runtime_type(type_name):
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('RuntimeTypeNotFoundError')(
                pipeline=pipeline, runtime_type_name=type_name
            )
        )

    return to_dauphin_runtime_type(pipeline.runtime_type_named(type_name))
