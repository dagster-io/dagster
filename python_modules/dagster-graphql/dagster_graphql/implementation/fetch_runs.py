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
    records = instance.get_run_records(PipelineRunsFilter(run_ids=[run_id]))
    if not records:
        return GrapheneRunNotFoundError(run_id)
    else:
        return GrapheneRun(records[0])


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
    run_group_run_ids = [run.run_id for run in run_group]
    records_by_id = {
        record.pipeline_run.run_id: record
        for record in instance.get_run_records(PipelineRunsFilter(run_ids=run_group_run_ids))
    }
    return GrapheneRunGroup(
        root_run_id=root_run_id,
        runs=[GrapheneRun(records_by_id.get(run_id)) for run_id in run_group_run_ids],
    )


def get_runs(graphene_info, filters, cursor=None, limit=None):
    from ..schema.pipelines.pipeline import GrapheneRun

    check.opt_inst_param(filters, "filters", PipelineRunsFilter)
    check.opt_str_param(cursor, "cursor")
    check.opt_int_param(limit, "limit")

    instance = graphene_info.context.instance

    return [
        GrapheneRun(record)
        for record in instance.get_run_records(filters=filters, cursor=cursor, limit=limit)
    ]


IN_PROGRESS_STATUSES = [
    PipelineRunStatus.STARTING,
    PipelineRunStatus.MANAGED,
    PipelineRunStatus.NOT_STARTED,
    PipelineRunStatus.QUEUED,
    PipelineRunStatus.STARTED,
    PipelineRunStatus.CANCELING,
]


def get_in_progress_runs_by_step(graphene_info, job_names, step_keys):
    from ..schema.pipelines.pipeline import GrapheneInProgressRunsByStep, GrapheneRun

    instance = graphene_info.context.instance

    in_progress_records = []
    for job_name in job_names:
        in_progress_records.extend(
            instance.get_run_records(
                PipelineRunsFilter(pipeline_name=job_name, statuses=IN_PROGRESS_STATUSES)
            )
        )

    in_progress_runs_by_step = {}
    unstarted_runs_by_step = {}

    for record in in_progress_records:
        run = record.pipeline_run
        step_stats = graphene_info.context.instance.get_run_step_stats(run.run_id, step_keys)
        for step_stat in step_stats:
            if step_stat.status == StepEventStatus.IN_PROGRESS:
                if step_stat.step_key not in in_progress_runs_by_step:
                    in_progress_runs_by_step[step_stat.step_key] = []
                in_progress_runs_by_step[step_stat.step_key].append(GrapheneRun(record))

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
                unstarted_runs_by_step[step_key].append(GrapheneRun(record))

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
    run_ids = {run.run_id for run_group in run_groups.values() for run in run_group.get("runs", [])}
    records_by_ids = {
        record.pipeline_run.run_id: record
        for record in instance.get_run_records(PipelineRunsFilter(run_ids=list(run_ids)))
    }

    for root_run_id in run_groups:
        run_groups[root_run_id]["runs"] = [
            GrapheneRun(records_by_ids.get(run.run_id)) for run in run_groups[root_run_id]["runs"]
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
