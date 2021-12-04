from dagster import PipelineDefinition, PipelineRunStatus, check
from dagster.config.validate import validate_config
from dagster.core.definitions import create_run_config_schema
from dagster.core.errors import DagsterRunNotFoundError
from dagster.core.execution.stats import StepEventStatus
from dagster.core.host_representation import PipelineSelector
from dagster.core.storage.pipeline_run import PipelineRunsFilter
from dagster.core.storage.tags import TagType, get_tag_type
from graphql.execution.base import ResolveInfo

from .external import ensure_valid_config, get_external_pipeline_or_raise
from .utils import UserFacingGraphQLError, capture_error


def is_config_valid(pipeline_def, run_config, mode):
    check.str_param(mode, "mode")
    check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition)

    run_config_schema = create_run_config_schema(pipeline_def, mode)
    validated_config = validate_config(run_config_schema.config_type, run_config)
    return validated_config.success


def get_validated_config(pipeline_def, run_config, mode):
    from ..schema.pipelines.config import GrapheneRunConfigValidationInvalid

    check.str_param(mode, "mode")
    check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition)

    run_config_schema = create_run_config_schema(pipeline_def, mode)

    validated_config = validate_config(run_config_schema.config_type, run_config)

    if not validated_config.success:
        raise UserFacingGraphQLError(
            GrapheneRunConfigValidationInvalid.for_validation_errors(
                pipeline_def.get_external_pipeline(), validated_config.errors
            )
        )

    return validated_config


def get_run_by_id(graphene_info, run_id):
    from ..schema.errors import GrapheneRunNotFoundError
    from ..schema.pipelines.pipeline import GrapheneRun

    instance = graphene_info.context.instance
    run = instance.get_run_by_id(run_id)
    if not run:
        return GrapheneRunNotFoundError(run_id)
    else:
        return GrapheneRun(run)


def get_run_tags(graphene_info):
    from ..schema.tags import GraphenePipelineTagAndValues

    instance = graphene_info.context.instance
    return [
        GraphenePipelineTagAndValues(key=key, values=values)
        for key, values in instance.get_run_tags()
        if get_tag_type(key) != TagType.HIDDEN
    ]


@capture_error
def get_run_group(graphene_info, run_id):
    from ..schema.errors import GrapheneRunGroupNotFoundError
    from ..schema.pipelines.pipeline import GrapheneRun
    from ..schema.runs import GrapheneRunGroup

    instance = graphene_info.context.instance
    try:
        result = instance.get_run_group(run_id)
    except DagsterRunNotFoundError:
        return GrapheneRunGroupNotFoundError(run_id)
    root_run_id, run_group = result
    return GrapheneRunGroup(root_run_id=root_run_id, runs=[GrapheneRun(run) for run in run_group])


def get_runs(graphene_info, filters, cursor=None, limit=None):
    from ..schema.pipelines.pipeline import GrapheneRun

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

    return [GrapheneRun(run) for run in runs]


def get_in_progress_runs_for_job(graphene_info, job_name):
    instance = graphene_info.context.instance

    in_progress_runs_filter = PipelineRunsFilter(
        pipeline_name=job_name,
        statuses=[
            PipelineRunStatus.STARTING,
            PipelineRunStatus.MANAGED,
            PipelineRunStatus.NOT_STARTED,
            PipelineRunStatus.QUEUED,
            PipelineRunStatus.STARTED,
            PipelineRunStatus.CANCELING,
        ],
    )

    return instance.get_runs(in_progress_runs_filter)


def get_in_progress_runs_by_step(graphene_info, in_progress_runs, step_keys):
    from ..schema.pipelines.pipeline import GrapheneInProgressRunsByStep, GrapheneRun

    in_progress_runs_by_step = {}
    unstarted_runs_by_step = {}

    for run in in_progress_runs:
        step_stats = graphene_info.context.instance.get_run_step_stats(run.run_id, step_keys)
        for step_stat in step_stats:
            if step_stat.status == StepEventStatus.IN_PROGRESS:
                if step_stat.step_key not in in_progress_runs_by_step:
                    in_progress_runs_by_step[step_stat.step_key] = []
                in_progress_runs_by_step[step_stat.step_key].append(GrapheneRun(run))

        asset_names = graphene_info.context.instance.get_execution_plan_snapshot(
            run.execution_plan_snapshot_id
        ).step_keys_to_execute

        for step_key in asset_names:
            # step_stats only contains stats for steps that are in progress or complete
            is_unstarted = (
                len([step_stat for step_stat in step_stats if step_stat.step_key == step_key]) == 0
            )
            if is_unstarted:
                if step_key not in unstarted_runs_by_step:
                    unstarted_runs_by_step[step_key] = []
                unstarted_runs_by_step[step_key].append(GrapheneRun(run))

    step_runs = []
    for key in in_progress_runs_by_step.keys() | unstarted_runs_by_step.keys():
        step_runs.append(
            GrapheneInProgressRunsByStep(
                key,
                unstarted_runs_by_step.get(key, []),
                in_progress_runs_by_step.get(key, []),
            )
        )

    return step_runs


def get_runs_count(graphene_info, filters):
    return graphene_info.context.instance.get_runs_count(filters)


def get_run_groups(graphene_info, filters=None, cursor=None, limit=None):
    from ..schema.pipelines.pipeline import GrapheneRun
    from ..schema.runs import GrapheneRunGroup

    check.opt_inst_param(filters, "filters", PipelineRunsFilter)
    check.opt_str_param(cursor, "cursor")
    check.opt_int_param(limit, "limit")

    instance = graphene_info.context.instance
    run_groups = instance.get_run_groups(filters=filters, cursor=cursor, limit=limit)

    for root_run_id in run_groups:
        run_groups[root_run_id]["runs"] = [
            GrapheneRun(run) for run in run_groups[root_run_id]["runs"]
        ]

    return [
        GrapheneRunGroup(root_run_id=root_run_id, runs=run_group["runs"])
        for root_run_id, run_group in run_groups.items()
    ]


@capture_error
def validate_pipeline_config(graphene_info, selector, run_config, mode):
    from ..schema.pipelines.config import GraphenePipelineConfigValidationValid

    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(selector, "selector", PipelineSelector)
    check.opt_str_param(mode, "mode")

    external_pipeline = get_external_pipeline_or_raise(graphene_info, selector)
    ensure_valid_config(external_pipeline, mode, run_config)
    return GraphenePipelineConfigValidationValid(pipeline_name=external_pipeline.name)


@capture_error
def get_execution_plan(graphene_info, selector, run_config, mode):
    from ..schema.execution import GrapheneExecutionPlan

    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(selector, "selector", PipelineSelector)
    check.opt_str_param(mode, "mode")

    external_pipeline = get_external_pipeline_or_raise(graphene_info, selector)
    ensure_valid_config(external_pipeline, mode, run_config)
    return GrapheneExecutionPlan(
        graphene_info.context.get_external_execution_plan(
            external_pipeline=external_pipeline,
            mode=mode,
            run_config=run_config,
            step_keys_to_execute=None,
            known_state=None,
        )
    )


@capture_error
def get_stats(graphene_info, run_id):
    from ..schema.pipelines.pipeline_run_stats import GrapheneRunStatsSnapshot

    stats = graphene_info.context.instance.get_run_stats(run_id)
    stats.id = "stats-{run_id}"
    return GrapheneRunStatsSnapshot(stats)


def get_step_stats(graphene_info, run_id, step_keys=None):
    from ..schema.logs.events import GrapheneRunStepStats

    step_stats = graphene_info.context.instance.get_run_step_stats(run_id, step_keys)
    return [GrapheneRunStepStats(stats) for stats in step_stats]
