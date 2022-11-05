from collections import defaultdict
from enum import Enum
from typing import TYPE_CHECKING, Dict, Iterable, KeysView, List, Mapping, Optional, cast

from dagster_graphql.implementation.fetch_assets import get_asset_nodes_by_asset_key
from graphene import ResolveInfo

from dagster import AssetKey
from dagster import _check as check
from dagster._config import validate_config
from dagster._core.definitions import create_run_config_schema
from dagster._core.errors import DagsterRunNotFoundError
from dagster._core.execution.stats import RunStepKeyStatsSnapshot, StepEventStatus
from dagster._core.host_representation import PipelineSelector
from dagster._core.storage.event_log.base import AssetRecord
from dagster._core.storage.pipeline_run import RunRecord, RunsFilter
from dagster._core.storage.tags import TagType, get_tag_type
from dagster._legacy import PipelineDefinition, PipelineRunStatus

from .events import from_event_record
from .external import ensure_valid_config, get_external_pipeline_or_raise
from .utils import UserFacingGraphQLError, capture_error

if TYPE_CHECKING:
    from ..schema.asset_graph import GrapheneAssetNode


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


class AssetComputeStatus(Enum):
    NONE = "NONE"
    UP_TO_DATE = "UP_TO_DATE"
    OUT_OF_DATE = "OUT_OF_DATE"


def add_all_upstream_keys(
    all_asset_nodes: Mapping[AssetKey, "GrapheneAssetNode"],
    requested_asset_keys: KeysView[AssetKey],
):
    required: Dict[AssetKey, bool] = {}

    def append_key_and_upstream(key: AssetKey):
        if required.get(key):
            return
        required[key] = True
        asset_node = all_asset_nodes[key].external_asset_node
        for dep in asset_node.dependencies:
            append_key_and_upstream(dep.upstream_asset_key)

    for asset_key in requested_asset_keys:
        append_key_and_upstream(asset_key)

    return required.keys()


def get_upstream_changed_by_asset(
    all_asset_nodes: Mapping[AssetKey, "GrapheneAssetNode"],
    all_asset_records: Iterable[AssetRecord],
    requested_asset_keys: KeysView[AssetKey],
):
    last_changed: Dict[AssetKey, float] = {}
    statuses: Dict[AssetKey, Optional[AssetComputeStatus]] = {}

    # First, iterate over all the asset records and build a dict of last materialization times.
    for asset_record in all_asset_records:
        asset_key = asset_record.asset_entry.asset_key
        if asset_record.asset_entry.last_materialization:
            last_changed[asset_key] = asset_record.asset_entry.last_materialization.timestamp

    # Beginning with the set of assets for which status was requested, recurse up the
    # dependency graphs and fill in statuses that are still `None`. Fill in the statuses
    # dict as we go to avoid traversing any part of the graph more then once. Note that for
    # A -> B -> C, if A is newer than B, both B and C are "old".
    #
    # Some assets (eg: source or partitioned assets) are not supported and get fixed statuses
    # the first time they're visited.
    #
    def fill_status_for(key: AssetKey):
        asset_node = all_asset_nodes[key].external_asset_node

        if not asset_node or not asset_node.op_names:
            return AssetComputeStatus.UP_TO_DATE  # source assets are always "up to date"
        if asset_node.partitions_def_data:
            return AssetComputeStatus.UP_TO_DATE  # partitioned assets are not supported
        elif not last_changed.get(key):
            return AssetComputeStatus.NONE  # never materialized assets cannot be stale

        # mark us out-of-date if upstream nodes have newer materialization times
        for dep in asset_node.dependencies:
            dep_key = dep.upstream_asset_key
            dep_node = all_asset_nodes[dep_key].external_asset_node
            if (
                last_changed.get(dep_key, 0) > last_changed.get(key, 0)
                and not dep_node.partitions_def_data
            ):
                return AssetComputeStatus.OUT_OF_DATE

        # cascade out-of-date / none states from upstream (more expensive than first scan)
        # Note: A materialized asset that depends on an asset that has never been materialized
        # gets an out-of-date state.
        for dep in asset_node.dependencies:
            if fill_or_return_status_for(dep.upstream_asset_key) != AssetComputeStatus.UP_TO_DATE:
                return AssetComputeStatus.OUT_OF_DATE

        return AssetComputeStatus.UP_TO_DATE

    def fill_or_return_status_for(key: AssetKey):
        if not statuses.get(key):
            statuses[key] = fill_status_for(key)
        return statuses[key]

    final: Dict[AssetKey, str] = {}
    for asset_key in requested_asset_keys:
        final[asset_key] = fill_or_return_status_for(asset_key)
    return final


def get_assets_latest_info(graphene_info, step_keys_by_asset: Mapping[AssetKey, List[str]]):
    from ..schema.asset_graph import GrapheneAssetLatestInfo
    from ..schema.logs.events import GrapheneMaterializationEvent
    from ..schema.pipelines.pipeline import GrapheneRun

    instance = graphene_info.context.instance

    asset_nodes = get_asset_nodes_by_asset_key(graphene_info)
    asset_record_keys_needed = add_all_upstream_keys(asset_nodes, step_keys_by_asset.keys())
    if not asset_record_keys_needed:
        return []

    asset_records = instance.get_asset_records(asset_record_keys_needed)
    upstream_changed_by_asset = get_upstream_changed_by_asset(
        asset_nodes, asset_records, step_keys_by_asset.keys()
    )

    latest_materialization_by_asset = {
        asset_record.asset_entry.asset_key: GrapheneMaterializationEvent(
            event=asset_record.asset_entry.last_materialization
        )
        if asset_record.asset_entry.last_materialization
        and asset_record.asset_entry.asset_key in step_keys_by_asset
        else None
        for asset_record in asset_records
    }

    latest_run_ids_by_asset: Dict[
        AssetKey, str
    ] = {  # last_run_id column is written to upon run creation (via ASSET_MATERIALIZATION_PLANNED event)
        asset_record.asset_entry.asset_key: asset_record.asset_entry.last_run_id
        for asset_record in asset_records
        if asset_record.asset_entry.last_run_id
    }

    run_records_by_run_id = {}
    in_progress_records = []
    run_ids = list(set(latest_run_ids_by_asset.values())) if latest_run_ids_by_asset else []
    if run_ids:
        run_records = instance.get_run_records(RunsFilter(run_ids=run_ids))
        for run_record in run_records:
            if run_record.pipeline_run.status in PENDING_STATUSES:
                in_progress_records.append(run_record)
            run_records_by_run_id[run_record.pipeline_run.run_id] = run_record

    (
        in_progress_run_ids_by_asset,
        unstarted_run_ids_by_asset,
    ) = _get_in_progress_runs_for_assets(graphene_info, in_progress_records, step_keys_by_asset)

    return [
        GrapheneAssetLatestInfo(
            asset_key,
            latest_materialization_by_asset.get(asset_key),
            (upstream_changed_by_asset.get(asset_key)),
            list(unstarted_run_ids_by_asset.get(asset_key, [])),
            list(in_progress_run_ids_by_asset.get(asset_key, [])),
            GrapheneRun(run_records_by_run_id[latest_run_ids_by_asset[asset_key]])
            # Dagit error occurs if a run is terminated at the same time that this endpoint is called
            # so we check to make sure the run ID exists in the run records
            if asset_key in latest_run_ids_by_asset
            and latest_run_ids_by_asset[asset_key] in run_records_by_run_id
            else None,
        )
        for asset_key in step_keys_by_asset.keys()
    ]


def _get_in_progress_runs_for_assets(
    graphene_info,
    in_progress_records: List[RunRecord],
    step_keys_by_asset: Mapping[AssetKey, List[str]],
):
    # Build mapping of step key to the assets it generates
    asset_key_by_step_key = defaultdict(set)
    for asset_key, step_keys in step_keys_by_asset.items():
        for step_key in step_keys:
            asset_key_by_step_key[step_key].add(asset_key)

    in_progress_run_ids_by_asset = defaultdict(set)
    unstarted_run_ids_by_asset = defaultdict(set)

    for record in in_progress_records:
        run = record.pipeline_run
        asset_selection = run.asset_selection
        run_step_keys = graphene_info.context.instance.get_execution_plan_snapshot(
            run.execution_plan_snapshot_id
        ).step_keys_to_execute

        selected_assets = (
            set.union(*[asset_key_by_step_key[run_step_key] for run_step_key in run_step_keys])
            if asset_selection is None
            else cast(frozenset, asset_selection)
        )  # only display in progress/unstarted indicators for selected assets

        if run.status in IN_PROGRESS_STATUSES:
            step_stats = graphene_info.context.instance.get_run_step_stats(
                run.run_id, run_step_keys
            )
            # Build mapping of asset to all the step stats that generate the asset
            step_stats_by_asset: Dict[AssetKey, List[RunStepKeyStatsSnapshot]] = defaultdict(list)
            for step_stat in step_stats:
                for asset_key in asset_key_by_step_key[step_stat.step_key]:
                    step_stats_by_asset[asset_key].append(step_stat)

            for asset in selected_assets:
                step_stats = step_stats_by_asset.get(asset)
                if step_stats:
                    # step_stats will contain all steps that are in progress or complete
                    if any(
                        [
                            step_stat.status == StepEventStatus.IN_PROGRESS
                            for step_stat in step_stats
                        ]
                    ):
                        in_progress_run_ids_by_asset[asset].add(record.pipeline_run.run_id)
                    # else if step_stats exist and none are in progress, the step has completed
                else:  # if step stats is none, then the step has not started
                    unstarted_run_ids_by_asset[asset].add(record.pipeline_run.run_id)
        else:
            # the run never began execution, all steps are unstarted
            for asset in selected_assets:
                unstarted_run_ids_by_asset[asset].add(record.pipeline_run.run_id)

    return in_progress_run_ids_by_asset, unstarted_run_ids_by_asset


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


@capture_error
def get_logs_for_run(graphene_info, run_id, cursor=None, limit=None):
    from ..schema.errors import GrapheneRunNotFoundError
    from ..schema.pipelines.pipeline import GrapheneEventConnection

    instance = graphene_info.context.instance
    run = instance.get_run_by_id(run_id)
    if not run:
        return GrapheneRunNotFoundError(run_id)

    conn = instance.get_records_for_run(run_id, cursor=cursor, limit=limit)
    return GrapheneEventConnection(
        events=[
            from_event_record(record.event_log_entry, run.pipeline_name) for record in conn.records
        ],
        cursor=conn.cursor,
        hasMore=conn.has_more,
    )
