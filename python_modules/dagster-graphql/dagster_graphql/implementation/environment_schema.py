from graphql.execution.base import ResolveInfo

from dagster import check
from dagster.config.validate import validate_config
from dagster.core.definitions.environment_schema import EnvironmentSchema, create_environment_schema
from dagster.core.definitions.pipeline import ExecutionSelector, PipelineDefinition

from .fetch_pipelines import get_pipeline_def_from_selector
from .utils import UserFacingGraphQLError, capture_dauphin_error


@capture_dauphin_error
def resolve_environment_schema_or_error(graphene_info, selector, mode):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)
    check.opt_str_param(mode, 'mode')

    pipeline_def = get_pipeline_def_from_selector(graphene_info, selector)

    if mode is None:
        mode = pipeline_def.get_default_mode_name()

    if not pipeline_def.has_mode_definition(mode):
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('ModeNotFoundError')(mode=mode, selector=selector)
        )

    return graphene_info.schema.type_named('EnvironmentSchema')(
        dagster_pipeline=pipeline_def,
        environment_schema=create_environment_schema(pipeline_def, mode),
    )


@capture_dauphin_error
def resolve_is_environment_config_valid(
    graphene_info, environment_schema, dagster_pipeline, environment_dict
):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(environment_schema, 'environment_schema', EnvironmentSchema)
    check.inst_param(dagster_pipeline, 'dagster_pipeline', PipelineDefinition)
    check.dict_param(environment_dict, 'environment_dict', key_type=str)

    validated_config = validate_config(environment_schema.environment_type, environment_dict)

    dauphin_pipeline = graphene_info.schema.type_named('Pipeline')(dagster_pipeline)

    if not validated_config.success:
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('PipelineConfigValidationInvalid')(
                pipeline=dauphin_pipeline,
                errors=[
                    graphene_info.schema.type_named(
                        'PipelineConfigValidationError'
                    ).from_dagster_error(
                        dagster_pipeline.get_config_schema_snapshot(), err,
                    )
                    for err in validated_config.errors
                ],
            )
        )

    return graphene_info.schema.type_named('PipelineConfigValidationValid')(dauphin_pipeline)
