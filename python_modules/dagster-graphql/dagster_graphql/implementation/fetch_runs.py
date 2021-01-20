from dagster import PipelineDefinition, check
from dagster.config.validate import validate_config
from dagster.core.definitions import create_run_config_schema
from dagster.core.host_representation import PipelineSelector
from dagster.core.storage.pipeline_run import PipelineRunsFilter
from dagster.core.storage.tags import TagType, get_tag_type
from graphql.execution.base import ResolveInfo

from .external import ensure_valid_config, get_external_pipeline_or_raise
from .utils import UserFacingGraphQLError, capture_dauphin_error


def is_config_valid(pipeline_def, run_config, mode):
    check.str_param(mode, "mode")
    check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition)

    run_config_schema = create_run_config_schema(pipeline_def, mode)
    validated_config = validate_config(run_config_schema.environment_type, run_config)
    return validated_config.success


def get_validated_config(pipeline_def, run_config, mode):
    from dagster_graphql.schema.errors import DauphinPipelineConfigValidationInvalid

    check.str_param(mode, "mode")
    check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition)

    run_config_schema = create_run_config_schema(pipeline_def, mode)

    validated_config = validate_config(run_config_schema.environment_type, run_config)

    if not validated_config.success:
        raise UserFacingGraphQLError(
            DauphinPipelineConfigValidationInvalid.for_validation_errors(
                pipeline_def.get_external_pipeline(), validated_config.errors
            )
        )

    return validated_config


def get_run_by_id(graphene_info, run_id):
    instance = graphene_info.context.instance
    run = instance.get_run_by_id(run_id)
    if not run:
        return graphene_info.schema.type_named("PipelineRunNotFoundError")(run_id)
    else:
        return graphene_info.schema.type_named("PipelineRun")(run)


def get_run_tags(graphene_info):
    instance = graphene_info.context.instance
    return [
        graphene_info.schema.type_named("PipelineTagAndValues")(key=key, values=values)
        for key, values in instance.get_run_tags()
        if get_tag_type(key) != TagType.HIDDEN
    ]


@capture_dauphin_error
def get_run_group(graphene_info, run_id):
    instance = graphene_info.context.instance
    result = instance.get_run_group(run_id)

    if result is None:
        return graphene_info.schema.type_named("RunGroupNotFoundError")(run_id)
    else:
        root_run_id, run_group = result
        return graphene_info.schema.type_named("RunGroup")(
            root_run_id=root_run_id,
            runs=[graphene_info.schema.type_named("PipelineRun")(run) for run in run_group],
        )


def get_runs(graphene_info, filters, cursor=None, limit=None):
    check.opt_inst_param(filters, "filters", PipelineRunsFilter)
    check.opt_str_param(cursor, "cursor")
    check.opt_int_param(limit, "limit")

    instance = graphene_info.context.instance
    runs = []

    if filters and filters.run_ids and len(filters.run_ids) == 1:
        run = instance.get_run_by_id(filters.run_ids[0])
        if run:
            runs = [run]
    elif filters and (
        filters.pipeline_name
        or filters.tags
        or filters.statuses
        or filters.snapshot_id
        or filters.run_ids
    ):
        runs = instance.get_runs(filters, cursor, limit)
    else:
        runs = instance.get_runs(cursor=cursor, limit=limit)

    return [graphene_info.schema.type_named("PipelineRun")(run) for run in runs]


def get_runs_count(graphene_info, filters):
    return graphene_info.context.instance.get_runs_count(filters)


def get_run_groups(graphene_info, filters=None, cursor=None, limit=None):
    from ..schema.runs import DauphinRunGroup

    check.opt_inst_param(filters, "filters", PipelineRunsFilter)
    check.opt_str_param(cursor, "cursor")
    check.opt_int_param(limit, "limit")

    instance = graphene_info.context.instance
    run_groups = instance.get_run_groups(filters=filters, cursor=cursor, limit=limit)

    for root_run_id in run_groups:
        run_groups[root_run_id]["runs"] = [
            graphene_info.schema.type_named("PipelineRun")(run)
            for run in run_groups[root_run_id]["runs"]
        ]

    return [
        DauphinRunGroup(root_run_id=root_run_id, runs=run_group["runs"])
        for root_run_id, run_group in run_groups.items()
    ]


@capture_dauphin_error
def validate_pipeline_config(graphene_info, selector, run_config, mode):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(selector, "selector", PipelineSelector)
    check.opt_str_param(mode, "mode")

    external_pipeline = get_external_pipeline_or_raise(graphene_info, selector)
    ensure_valid_config(external_pipeline, mode, run_config)
    return graphene_info.schema.type_named("PipelineConfigValidationValid")(
        pipeline_name=external_pipeline.name
    )


@capture_dauphin_error
def get_execution_plan(graphene_info, selector, run_config, mode):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(selector, "selector", PipelineSelector)
    check.opt_str_param(mode, "mode")

    external_pipeline = get_external_pipeline_or_raise(graphene_info, selector)
    ensure_valid_config(external_pipeline, mode, run_config)
    return graphene_info.schema.type_named("ExecutionPlan")(
        graphene_info.context.get_external_execution_plan(
            external_pipeline=external_pipeline,
            mode=mode,
            run_config=run_config,
            step_keys_to_execute=None,
        )
    )


@capture_dauphin_error
def get_stats(graphene_info, run_id):
    stats = graphene_info.context.instance.get_run_stats(run_id)
    stats.id = "stats-{run_id}"
    return graphene_info.schema.type_named("PipelineRunStatsSnapshot")(stats)


def get_step_stats(graphene_info, run_id, step_keys=None):
    step_stats = graphene_info.context.instance.get_run_step_stats(run_id, step_keys)
    return [graphene_info.schema.type_named("PipelineRunStepStats")(stats) for stats in step_stats]
