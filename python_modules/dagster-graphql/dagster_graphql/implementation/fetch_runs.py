from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Dict,
    KeysView,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
    cast,
)

from dagster import (
    AssetKey,
    _check as check,
)
from dagster._core.definitions.selector import JobSubsetSelector
from dagster._core.errors import DagsterRunNotFoundError
from dagster._core.execution.stats import RunStepKeyStatsSnapshot, StepEventStatus
from dagster._core.storage.dagster_run import DagsterRunStatus, RunRecord, RunsFilter
from dagster._core.storage.tags import TagType, get_tag_type

from .external import ensure_valid_config, get_external_job_or_raise

if TYPE_CHECKING:
    from ..schema.asset_graph import GrapheneAssetLatestInfo, GrapheneAssetNode
    from ..schema.errors import GrapheneRunNotFoundError
    from ..schema.execution import GrapheneExecutionPlan
    from ..schema.logs.events import GrapheneRunStepStats
    from ..schema.pipelines.config import GraphenePipelineConfigValidationValid
    from ..schema.pipelines.pipeline import GrapheneEventConnection, GrapheneRun
    from ..schema.pipelines.pipeline_run_stats import GrapheneRunStatsSnapshot
    from ..schema.runs import GrapheneRunGroup, GrapheneRunTagKeys, GrapheneRunTags
    from ..schema.util import ResolveInfo


def get_run_by_id(
    graphene_info: "ResolveInfo", run_id: str
) -> Union["GrapheneRun", "GrapheneRunNotFoundError"]:
    from ..schema.errors import GrapheneRunNotFoundError
    from ..schema.pipelines.pipeline import GrapheneRun

    instance = graphene_info.context.instance
    record = instance.get_run_record_by_id(run_id)
    if not record:
        return GrapheneRunNotFoundError(run_id)
    else:
        return GrapheneRun(record)


def get_run_tag_keys(graphene_info: "ResolveInfo") -> "GrapheneRunTagKeys":
    from ..schema.runs import GrapheneRunTagKeys

    return GrapheneRunTagKeys(
        keys=[
            tag_key
            for tag_key in graphene_info.context.instance.get_run_tag_keys()
            if get_tag_type(tag_key) != TagType.HIDDEN
        ]
    )


def get_run_tags(
    graphene_info: "ResolveInfo",
    tag_keys: Optional[List[str]] = None,
    value_prefix: Optional[str] = None,
    limit: Optional[int] = None,
) -> "GrapheneRunTags":
    from ..schema.runs import GrapheneRunTags
    from ..schema.tags import GraphenePipelineTagAndValues

    instance = graphene_info.context.instance
    return GrapheneRunTags(
        tags=[
            GraphenePipelineTagAndValues(key=key, values=values)
            for key, values in instance.get_run_tags(
                tag_keys=tag_keys, value_prefix=value_prefix, limit=limit
            )
            if get_tag_type(key) != TagType.HIDDEN
        ]
    )


def get_run_group(graphene_info: "ResolveInfo", run_id: str) -> "GrapheneRunGroup":
    from ..schema.errors import GrapheneRunGroupNotFoundError
    from ..schema.pipelines.pipeline import GrapheneRun
    from ..schema.runs import GrapheneRunGroup

    instance = graphene_info.context.instance
    try:
        result = instance.get_run_group(run_id)
        if result is None:
            return GrapheneRunGroupNotFoundError(run_id)
    except DagsterRunNotFoundError:
        return GrapheneRunGroupNotFoundError(run_id)
    root_run_id, run_group = result
    run_group_run_ids = [run.run_id for run in run_group]
    records_by_id = {
        record.dagster_run.run_id: record
        for record in instance.get_run_records(RunsFilter(run_ids=run_group_run_ids))
    }
    return GrapheneRunGroup(
        root_run_id=root_run_id,
        runs=[GrapheneRun(records_by_id[run_id]) for run_id in run_group_run_ids],
    )


def get_runs(
    graphene_info: "ResolveInfo",
    filters: Optional[RunsFilter],
    cursor: Optional[str] = None,
    limit: Optional[int] = None,
) -> Sequence["GrapheneRun"]:
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
    DagsterRunStatus.STARTING,
    DagsterRunStatus.MANAGED,
    DagsterRunStatus.NOT_STARTED,
    DagsterRunStatus.QUEUED,
    DagsterRunStatus.STARTED,
    DagsterRunStatus.CANCELING,
]
IN_PROGRESS_STATUSES = [
    DagsterRunStatus.STARTED,
    DagsterRunStatus.CANCELING,
]


def add_all_upstream_keys(
    all_asset_nodes: Mapping[AssetKey, "GrapheneAssetNode"],
    requested_asset_keys: KeysView[AssetKey],
) -> Sequence[AssetKey]:
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

    return list(required.keys())


def get_assets_latest_info(
    graphene_info: "ResolveInfo", step_keys_by_asset: Mapping[AssetKey, Sequence[str]]
) -> Sequence["GrapheneAssetLatestInfo"]:
    from dagster_graphql.implementation.fetch_assets import get_asset_nodes_by_asset_key

    from ..schema.asset_graph import GrapheneAssetLatestInfo
    from ..schema.logs.events import GrapheneMaterializationEvent
    from ..schema.pipelines.pipeline import GrapheneRun

    instance = graphene_info.context.instance

    asset_nodes = get_asset_nodes_by_asset_key(graphene_info)
    asset_record_keys_needed = add_all_upstream_keys(asset_nodes, step_keys_by_asset.keys())
    if not asset_record_keys_needed:
        return []

    asset_records = instance.get_asset_records(asset_record_keys_needed)

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
            if run_record.dagster_run.status in PENDING_STATUSES:
                in_progress_records.append(run_record)
            run_records_by_run_id[run_record.dagster_run.run_id] = run_record

    (
        in_progress_run_ids_by_asset,
        unstarted_run_ids_by_asset,
    ) = _get_in_progress_runs_for_assets(graphene_info, in_progress_records, step_keys_by_asset)

    return [
        GrapheneAssetLatestInfo(
            asset_key,
            latest_materialization_by_asset.get(asset_key),
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
    graphene_info: "ResolveInfo",
    in_progress_records: Sequence[RunRecord],
    step_keys_by_asset: Mapping[AssetKey, Sequence[str]],
) -> Tuple[Mapping[AssetKey, AbstractSet[str]], Mapping[AssetKey, AbstractSet[str]]]:
    # Build mapping of step key to the assets it generates
    asset_key_by_step_key = defaultdict(set)
    for asset_key, step_keys in step_keys_by_asset.items():
        for step_key in step_keys:
            asset_key_by_step_key[step_key].add(asset_key)

    in_progress_run_ids_by_asset = defaultdict(set)
    unstarted_run_ids_by_asset = defaultdict(set)

    for record in in_progress_records:
        run = record.dagster_run
        asset_selection = run.asset_selection
        run_step_keys = graphene_info.context.instance.get_execution_plan_snapshot(
            check.not_none(run.execution_plan_snapshot_id)
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
                asset_step_stats = step_stats_by_asset.get(asset)
                if asset_step_stats:
                    # asset_step_stats will contain all steps that are in progress or complete
                    if any(
                        [
                            step_stat.status == StepEventStatus.IN_PROGRESS
                            for step_stat in asset_step_stats
                        ]
                    ):
                        in_progress_run_ids_by_asset[asset].add(record.dagster_run.run_id)
                    # else if step_stats exist and none are in progress, the step has completed
                else:  # if step stats is none, then the step has not started
                    unstarted_run_ids_by_asset[asset].add(record.dagster_run.run_id)
        else:
            # the run never began execution, all steps are unstarted
            for asset in selected_assets:
                unstarted_run_ids_by_asset[asset].add(record.dagster_run.run_id)

    return in_progress_run_ids_by_asset, unstarted_run_ids_by_asset


def get_runs_count(graphene_info: "ResolveInfo", filters: Optional[RunsFilter]) -> int:
    return graphene_info.context.instance.get_runs_count(filters)


def get_run_groups(
    graphene_info: "ResolveInfo",
    filters: Optional[RunsFilter] = None,
    cursor: Optional[str] = None,
    limit: Optional[int] = None,
) -> Sequence["GrapheneRunGroup"]:
    from ..schema.pipelines.pipeline import GrapheneRun
    from ..schema.runs import GrapheneRunGroup

    check.opt_inst_param(filters, "filters", RunsFilter)
    check.opt_str_param(cursor, "cursor")
    check.opt_int_param(limit, "limit")

    instance = graphene_info.context.instance
    run_groups = instance.get_run_groups(filters=filters, cursor=cursor, limit=limit)
    run_ids = {run.run_id for run_group in run_groups.values() for run in run_group.get("runs", [])}
    records_by_ids = {
        record.dagster_run.run_id: record
        for record in instance.get_run_records(RunsFilter(run_ids=list(run_ids)))
    }

    for root_run_id in run_groups:
        run_groups[root_run_id]["runs"] = [
            GrapheneRun(records_by_ids[run.run_id]) for run in run_groups[root_run_id]["runs"]
        ]

    return [
        GrapheneRunGroup(root_run_id=root_run_id, runs=run_group["runs"])
        for root_run_id, run_group in run_groups.items()
    ]


def validate_pipeline_config(
    graphene_info: "ResolveInfo",
    selector: JobSubsetSelector,
    run_config: Union[str, Mapping[str, object]],
) -> "GraphenePipelineConfigValidationValid":
    from ..schema.pipelines.config import GraphenePipelineConfigValidationValid

    check.inst_param(selector, "selector", JobSubsetSelector)

    external_job = get_external_job_or_raise(graphene_info, selector)
    ensure_valid_config(external_job, run_config)
    return GraphenePipelineConfigValidationValid(pipeline_name=external_job.name)


def get_execution_plan(
    graphene_info: "ResolveInfo",
    selector: JobSubsetSelector,
    run_config: Mapping[str, Any],
) -> "GrapheneExecutionPlan":
    from ..schema.execution import GrapheneExecutionPlan

    check.inst_param(selector, "selector", JobSubsetSelector)

    external_job = get_external_job_or_raise(graphene_info, selector)
    ensure_valid_config(external_job, run_config)
    return GrapheneExecutionPlan(
        graphene_info.context.get_external_execution_plan(
            external_job=external_job,
            run_config=run_config,
            step_keys_to_execute=None,
            known_state=None,
        )
    )


def get_stats(graphene_info: "ResolveInfo", run_id: str) -> "GrapheneRunStatsSnapshot":
    from ..schema.pipelines.pipeline_run_stats import GrapheneRunStatsSnapshot

    stats = graphene_info.context.instance.get_run_stats(run_id)
    stats.id = "stats-{run_id}"  # type: ignore  # (unused code path)
    return GrapheneRunStatsSnapshot(stats)


def get_step_stats(
    graphene_info: "ResolveInfo", run_id: str, step_keys: Optional[Sequence[str]] = None
) -> Sequence["GrapheneRunStepStats"]:
    from ..schema.logs.events import GrapheneRunStepStats

    step_stats = graphene_info.context.instance.get_run_step_stats(run_id, step_keys)
    return [GrapheneRunStepStats(stats) for stats in step_stats]


def get_logs_for_run(
    graphene_info: "ResolveInfo",
    run_id: str,
    cursor: Optional[str] = None,
    limit: Optional[int] = None,
) -> Union["GrapheneRunNotFoundError", "GrapheneEventConnection"]:
    from ..schema.errors import GrapheneRunNotFoundError
    from ..schema.pipelines.pipeline import GrapheneEventConnection
    from .events import from_event_record

    instance = graphene_info.context.instance
    run = instance.get_run_by_id(run_id)
    if not run:
        return GrapheneRunNotFoundError(run_id)

    conn = instance.get_records_for_run(run_id, cursor=cursor, limit=limit)
    return GrapheneEventConnection(
        events=[from_event_record(record.event_log_entry, run.job_name) for record in conn.records],
        cursor=conn.cursor,
        hasMore=conn.has_more,
    )
