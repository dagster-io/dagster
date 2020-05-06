from graphql.execution.base import ResolveInfo

from dagster import check
from dagster.config.validate import validate_config_from_snap
from dagster.core.definitions.pipeline import ExecutionSelector
from dagster.core.snap import PipelineIndex

from .external import get_external_pipeline_subset_or_raise
from .utils import UserFacingGraphQLError, capture_dauphin_error


@capture_dauphin_error
def resolve_environment_schema_or_error(graphene_info, selector, mode):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)
    check.opt_str_param(mode, 'mode')

    pipeline_index = get_external_pipeline_subset_or_raise(
        graphene_info, selector.name, selector.solid_subset
    ).pipeline_index

    if mode is None:
        mode = pipeline_index.get_default_mode_name()

    if not pipeline_index.has_mode_def(mode):
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('ModeNotFoundError')(mode=mode, selector=selector)
        )

    return graphene_info.schema.type_named('EnvironmentSchema')(
        pipeline_index=pipeline_index, mode=mode,
    )


@capture_dauphin_error
def resolve_is_environment_config_valid(graphene_info, pipeline_index, mode, environment_dict):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(pipeline_index, 'pipeline_index', PipelineIndex)
    check.str_param(mode, 'mode')
    check.dict_param(environment_dict, 'environment_dict', key_type=str)

    mode_def_snap = pipeline_index.get_mode_def_snap(mode)

    if not mode_def_snap.root_config_key:
        # historical pipeline with unknown environment type. blindly pass validation
        return graphene_info.schema.type_named('PipelineConfigValidationValid')(pipeline_index.name)

    validated_config = validate_config_from_snap(
        pipeline_index.config_schema_snapshot, mode_def_snap.root_config_key, environment_dict
    )

    if not validated_config.success:
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('PipelineConfigValidationInvalid')(
                pipeline_name=pipeline_index.name,
                errors=[
                    graphene_info.schema.type_named(
                        'PipelineConfigValidationError'
                    ).from_dagster_error(
                        pipeline_index.config_schema_snapshot, err,
                    )
                    for err in validated_config.errors
                ],
            )
        )

    return graphene_info.schema.type_named('PipelineConfigValidationValid')(pipeline_index.name)
