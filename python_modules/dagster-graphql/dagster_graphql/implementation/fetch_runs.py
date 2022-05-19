from collections import defaultdict
from typing import Dict

from graphql.execution.base import ResolveInfo

from dagster import AssetKey, PipelineDefinition, PipelineRunStatus
from dagster import _check as check
from dagster.config.validate import validate_config
from dagster.core.definitions import create_run_config_schema
from dagster.core.errors import DagsterRunNotFoundError
from dagster.core.execution.stats import StepEventStatus
from dagster.core.host_representation import PipelineSelector
from dagster.core.storage.pipeline_run import PipelineRun, RunsFilter
from dagster.core.storage.tags import TagType, get_tag_type
from dagster.core.execution.stats import RunStepKeyStatsSnapshot

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
    records = instance.get_run_records(RunsFilter(run_ids=[run_id]))
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
        for record in instance.get_run_records(RunsFilter(run_ids=run_group_run_ids))
    }
    return GrapheneRunGroup(
        root_run_id=root_run_id,
        runs=[GrapheneRun(records_by_id.get(run_id)) for run_id in run_group_run_ids],
    )


def get_runs(graphene_info, filters, cursor=None, limit=None):
    from ..schema.pipelines.pipeline import GrapheneRun

    check.opt_inst_param(filters, "filters", RunsFilter)
    check.opt_str_param(cursor, "cursor")
    check.opt_int_param(limit, "limit")

    instance = graphene_info.context.instance

    return [
        GrapheneRun(record)
        for record in instance.get_run_records(filters=filters, cursor=cursor, limit=limit)
    ]


PENDING_STATUSES = [
    PipelineRunStatus.STARTING,
    PipelineRunStatus.MANAGED,
    PipelineRunStatus.NOT_STARTED,
    PipelineRunStatus.QUEUED,
    PipelineRunStatus.STARTED,
    PipelineRunStatus.CANCELING,
]
IN_PROGRESS_STATUSES = [
    PipelineRunStatus.STARTED,
    PipelineRunStatus.CANCELING,
]


def get_in_progress_runs_by_asset(graphene_info, job_names, step_keys_by_asset):
    from ..schema.pipelines.pipeline import GrapheneInProgressRunsByAsset, GrapheneRun

    instance = graphene_info.context.instance

    # TODO check if pipeline run is generating the asset
    asset_key_by_step_key = defaultdict(set)
    for asset_key, step_keys in step_keys_by_asset.items():
        for step_key in step_keys:
            asset_key_by_step_key[step_key].add(asset_key)

    in_progress_records = []
    for job_name in job_names:
        in_progress_records.extend(
            instance.get_run_records(RunsFilter(pipeline_name=job_name, statuses=PENDING_STATUSES))
        )

    in_progress_runs_by_asset = defaultdict(set)
    unstarted_runs_by_asset = defaultdict(set)

    asset_step_keys = set()
    for step_keys_for_asset in step_keys_by_asset.values():
        asset_step_keys = asset_step_keys.union(set(step_keys_for_asset))

    for record in in_progress_records:
        run = record.pipeline_run

        run_step_keys = graphene_info.context.instance.get_execution_plan_snapshot(
            run.execution_plan_snapshot_id
        ).step_keys_to_execute

        run_generates_assets = len(set(run_step_keys).intersection(asset_step_keys)) > 0

        if run_generates_assets:
            if run.status in IN_PROGRESS_STATUSES:
                step_stats = graphene_info.context.instance.get_run_step_stats(
                    run.run_id, run_step_keys
                )
                step_stats_by_asset: Dict[AssetKey, List[RunStepKeyStatsSnapshot]] = defaultdict(
                    list
                )
                for step_stat in step_stats:
                    asset_keys = asset_key_by_step_key[step_stat.step_key]
                    for asset_key in asset_keys:
                        step_stats_by_asset[asset_key].append(step_stat)

                for asset in step_keys_by_asset.keys():
                    step_stats = step_stats_by_asset[asset]
                    if any(
                        [
                            step_stat.status == StepEventStatus.IN_PROGRESS
                            for step_stat in step_stats
                        ]
                    ):
                        in_progress_runs_by_asset[asset].add(GrapheneRun(record))
                    elif len(step_stats) == 0:
                        unstarted_runs_by_asset[asset].add(GrapheneRun(record))
            else:
                # the run never began execution, all steps are unstarted
                for step_key in run_step_keys:
                    for asset_key in asset_key_by_step_key[step_key]:
                        unstarted_runs_by_asset[asset_key].add(GrapheneRun(record))

    all_assets = in_progress_runs_by_asset.keys() | unstarted_runs_by_asset.keys()

    for asset_key in all_assets:
        print(asset_key)
        print(unstarted_runs_by_asset.get(asset_key, []))
        print(in_progress_runs_by_asset.get(asset_key, []))

    return [
        GrapheneInProgressRunsByAsset(
            asset_key,
            list(unstarted_runs_by_asset.get(asset_key, [])),
            list(in_progress_runs_by_asset.get(asset_key, [])),
        )
        for asset_key in all_assets
    ]


def get_latest_asset_run_by_step_key(graphene_info, asset_nodes):
    from ..schema.pipelines.pipeline import GrapheneLatestRun, GrapheneRun

    instance = graphene_info.context.instance

    latest_run_by_step: Dict[str, PipelineRun] = {}
    latest_run_id_by_asset: Dict[AssetKey, str] = {}

    for record in instance.get_asset_records([asset.asset_key for asset in asset_nodes]):
        asset_key = record.asset_entry.asset_key
        last_run_id = record.asset_entry.last_run_id
        if last_run_id:
            latest_run_id_by_asset[asset_key] = last_run_id

    run_records_by_run_id = {}
    run_ids = list(set(latest_run_id_by_asset.values()))
    if run_ids:
        run_records = instance.get_run_records(RunsFilter(run_ids=run_ids))
        for run_record in run_records:
            run_records_by_run_id[run_record.pipeline_run.run_id] = run_record

    for asset in asset_nodes:
        run_id = latest_run_id_by_asset.get(asset.asset_key)
        step_key = asset.op_name
        # return run = None when no runs have occurred for the asset
        latest_run_by_step[step_key] = GrapheneLatestRun(
            step_key, GrapheneRun(run_records_by_run_id[run_id]) if run_id else None
        )

    return [latest_run_by_step.get(asset_node.op_name) for asset_node in asset_nodes]


def get_runs_count(graphene_info, filters):
    return graphene_info.context.instance.get_runs_count(filters)


def get_run_groups(graphene_info, filters=None, cursor=None, limit=None):
    from ..schema.pipelines.pipeline import GrapheneRun
    from ..schema.runs import GrapheneRunGroup

    check.opt_inst_param(filters, "filters", RunsFilter)
    check.opt_str_param(cursor, "cursor")
    check.opt_int_param(limit, "limit")

    instance = graphene_info.context.instance
    run_groups = instance.get_run_groups(filters=filters, cursor=cursor, limit=limit)
    run_ids = {run.run_id for run_group in run_groups.values() for run in run_group.get("runs", [])}
    records_by_ids = {
        record.pipeline_run.run_id: record
        for record in instance.get_run_records(RunsFilter(run_ids=list(run_ids)))
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
