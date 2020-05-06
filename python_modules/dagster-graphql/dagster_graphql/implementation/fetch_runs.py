from graphql.execution.base import ResolveInfo

from dagster import PipelineDefinition, check
from dagster.config.validate import validate_config
from dagster.core.definitions import create_environment_schema
from dagster.core.definitions.pipeline import ExecutionSelector
from dagster.core.storage.pipeline_run import PipelineRunsFilter

from .external import ensure_valid_config, get_external_pipeline_subset_or_raise
from .utils import UserFacingGraphQLError, capture_dauphin_error


def is_config_valid(pipeline_def, environment_dict, mode):
    check.str_param(mode, 'mode')
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)

    environment_schema = create_environment_schema(pipeline_def, mode)
    validated_config = validate_config(environment_schema.environment_type, environment_dict)
    return validated_config.success


def get_validated_config(pipeline_def, environment_dict, mode):
    from dagster_graphql.schema.errors import DauphinPipelineConfigValidationInvalid

    check.str_param(mode, 'mode')
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)

    environment_schema = create_environment_schema(pipeline_def, mode)

    validated_config = validate_config(environment_schema.environment_type, environment_dict)

    if not validated_config.success:
        raise UserFacingGraphQLError(
            DauphinPipelineConfigValidationInvalid.for_validation_errors(
                pipeline_def.get_pipeline_index(), validated_config.errors
            )
        )

    return validated_config


def get_run_by_id(graphene_info, run_id):
    instance = graphene_info.context.instance
    run = instance.get_run_by_id(run_id)
    if not run:
        return graphene_info.schema.type_named('PipelineRunNotFoundError')(run_id)
    else:
        return graphene_info.schema.type_named('PipelineRun')(run)


def get_run_tags(graphene_info):
    instance = graphene_info.context.instance
    return [
        graphene_info.schema.type_named('PipelineTagAndValues')(key=key, values=values)
        for key, values in instance.get_run_tags()
    ]


@capture_dauphin_error
def get_run_group(graphene_info, run_id):
    instance = graphene_info.context.instance
    result = instance.get_run_group(run_id)

    if result is None:
        return graphene_info.schema.type_named('RunGroupNotFoundError')(run_id)
    else:
        root_run_id, run_group = result
        return graphene_info.schema.type_named('RunGroup')(
            root_run_id=root_run_id,
            runs=[graphene_info.schema.type_named('PipelineRun')(run) for run in run_group],
        )


def get_runs(graphene_info, filters, cursor=None, limit=None):
    check.opt_inst_param(filters, 'filters', PipelineRunsFilter)
    check.opt_str_param(cursor, 'cursor')
    check.opt_int_param(limit, 'limit')

    instance = graphene_info.context.instance
    runs = []

    if filters and filters.run_ids and len(filters.run_ids) == 1:
        run = instance.get_run_by_id(filters.run_ids[0])
        if run:
            runs = [run]
    elif filters and (filters.pipeline_name or filters.tags or filters.status):
        runs = instance.get_runs(filters, cursor, limit)
    else:
        runs = instance.get_runs(cursor=cursor, limit=limit)

    return [graphene_info.schema.type_named('PipelineRun')(run) for run in runs]


@capture_dauphin_error
def validate_pipeline_config(graphene_info, selector, environment_dict, mode):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)
    check.opt_str_param(mode, 'mode')

    external_pipeline = get_external_pipeline_subset_or_raise(
        graphene_info, selector.name, selector.solid_subset
    )
    ensure_valid_config(external_pipeline, mode, environment_dict)
    return graphene_info.schema.type_named('PipelineConfigValidationValid')(
        pipeline_name=external_pipeline.name
    )


@capture_dauphin_error
def get_execution_plan(graphene_info, selector, environment_dict, mode):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)
    check.opt_str_param(mode, 'mode')

    external_pipeline = get_external_pipeline_subset_or_raise(
        graphene_info, selector.name, selector.solid_subset
    )
    ensure_valid_config(external_pipeline, mode, environment_dict)
    return graphene_info.schema.type_named('ExecutionPlan')(
        graphene_info.context.create_execution_plan_index(
            external_pipeline=external_pipeline, mode=mode, environment_dict=environment_dict
        )
    )


@capture_dauphin_error
def get_stats(graphene_info, run_id):
    stats = graphene_info.context.instance.get_run_stats(run_id)
    return graphene_info.schema.type_named('PipelineRunStatsSnapshot')(stats)


def get_step_stats(graphene_info, run_id):
    step_stats = graphene_info.context.instance.get_run_step_stats(run_id)
    return [graphene_info.schema.type_named('PipelineRunStepStats')(stats) for stats in step_stats]
