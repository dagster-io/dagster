from graphql.execution.base import ResolveInfo

from dagster import check
from dagster.core.execution.api import ExecutionSelector
from dagster.core.definitions.environment_schema import create_environment_schema, EnvironmentSchema
from dagster.core.definitions.pipeline import PipelineDefinition
from dagster.core.types.evaluator import evaluate_config
from .fetch_pipelines import get_dagster_pipeline_from_selector
from .utils import capture_dauphin_error, UserFacingGraphQLError


@capture_dauphin_error
def resolve_environment_schema_or_error(graphene_info, selector, mode):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)

    dagster_pipeline = get_dagster_pipeline_from_selector(graphene_info, selector)

    if not dagster_pipeline.has_mode_definition(mode):
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('ModeNotFoundError')(mode=mode, selector=selector)
        )

    return graphene_info.schema.type_named('EnvironmentSchema')(
        dagster_pipeline=dagster_pipeline,
        environment_schema=create_environment_schema(dagster_pipeline, mode),
    )


@capture_dauphin_error
def resolve_config_type_or_error(
    graphene_info, environment_schema, dagster_pipeline, config_type_name
):
    from dagster_graphql.schema.config_types import to_dauphin_config_type

    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(environment_schema, 'environment_scheam', EnvironmentSchema)
    check.inst_param(dagster_pipeline, 'dagster_pipeline', PipelineDefinition)
    check.str_param(config_type_name, 'config_type_name')

    if not environment_schema.has_config_type(config_type_name):
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('ConfigTypeNotFoundError')(
                pipeline=dagster_pipeline, config_type_name=config_type_name
            )
        )

    return to_dauphin_config_type(environment_schema.config_type_named(config_type_name))


@capture_dauphin_error
def resolve_is_environment_config_valid(
    graphene_info, environment_schema, dagster_pipeline, environment_dict
):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(environment_schema, 'environment_schema', EnvironmentSchema)
    check.inst_param(dagster_pipeline, 'dagster_pipeline', PipelineDefinition)
    check.opt_dict_param(environment_dict, 'environment_dict', key_type=str)

    validated_config = evaluate_config(
        environment_schema.environment_type, environment_dict, dagster_pipeline
    )

    dauphin_pipeline = graphene_info.schema.type_named('Pipeline')(dagster_pipeline)

    if not validated_config.success:
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('PipelineConfigValidationInvalid')(
                pipeline=dauphin_pipeline,
                errors=[
                    graphene_info.schema.type_named(
                        'PipelineConfigValidationError'
                    ).from_dagster_error(graphene_info, err)
                    for err in validated_config.errors
                ],
            )
        )

    return graphene_info.schema.type_named('PipelineConfigValidationValid')(dauphin_pipeline)
