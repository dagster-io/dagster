from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
)

from dagster import (
    AssetKey,
    _check as check,
)
from dagster._core.definitions.selector import JobSubsetSelector
from dagster._core.errors import DagsterRunNotFoundError
from dagster._core.instance import DagsterInstance
from dagster._core.storage.dagster_run import DagsterRunStatus, RunRecord, RunsFilter
from dagster._core.storage.event_log.base import AssetRecord
from dagster._core.storage.tags import TagType, get_tag_type

from .external import ensure_valid_config, get_external_job_or_raise

if TYPE_CHECKING:
    from dagster._core.storage.batch_asset_record_loader import BatchAssetRecordLoader

    from ..schema.asset_graph import GrapheneAssetLatestInfo
    from ..schema.errors import GrapheneRunNotFoundError
    from ..schema.execution import GrapheneExecutionPlan
    from ..schema.logs.events import GrapheneRunStepStats
    from ..schema.pipelines.config import GraphenePipelineConfigValidationValid
    from ..schema.pipelines.pipeline import GrapheneEventConnection, GrapheneRun
    from ..schema.pipelines.pipeline_run_stats import GrapheneRunStatsSnapshot
    from ..schema.runs import GrapheneRunGroup, GrapheneRunTagKeys, GrapheneRunTags
    from ..schema.util import ResolveInfo


async def gen_run_by_id(
    graphene_info: "ResolveInfo", run_id: str
) -> Union["GrapheneRun", "GrapheneRunNotFoundError"]:
    from ..schema.errors import GrapheneRunNotFoundError
    from ..schema.pipelines.pipeline import GrapheneRun

    record = await RunRecord.gen(graphene_info.context, run_id)
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
    tag_keys: List[str],
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


def get_run_ids(
    graphene_info: "ResolveInfo",
    filters: Optional[RunsFilter],
    cursor: Optional[str] = None,
    limit: Optional[int] = None,
) -> Sequence[str]:
    check.opt_inst_param(filters, "filters", RunsFilter)
    check.opt_str_param(cursor, "cursor")
    check.opt_int_param(limit, "limit")

    instance = graphene_info.context.instance

    return instance.get_run_ids(filters=filters, cursor=cursor, limit=limit)


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


def _get_latest_planned_run_id(instance: DagsterInstance, asset_record: AssetRecord):
    if instance.event_log_storage.asset_records_have_last_planned_materialization_storage_id:
        return asset_record.asset_entry.last_planned_materialization_run_id
    else:
        planned_info = instance.get_latest_planned_materialization_info(
            asset_record.asset_entry.asset_key
        )
        return planned_info.run_id if planned_info else None


def get_assets_latest_info(
    graphene_info: "ResolveInfo",
    asset_keys: Sequence[AssetKey],
    asset_record_loader: "BatchAssetRecordLoader",
) -> Sequence["GrapheneAssetLatestInfo"]:
    from ..schema.asset_graph import GrapheneAssetLatestInfo
    from ..schema.logs.events import GrapheneMaterializationEvent
    from ..schema.pipelines.pipeline import GrapheneRun

    instance = graphene_info.context.instance

    if not asset_keys:
        return []

    asset_key_set = set(asset_keys)

    asset_records = asset_record_loader.get_asset_records(asset_keys)

    latest_materialization_by_asset = {
        asset_record.asset_entry.asset_key: (
            GrapheneMaterializationEvent(event=asset_record.asset_entry.last_materialization)
            if asset_record.asset_entry.last_materialization
            and asset_record.asset_entry.asset_key in asset_key_set
            else None
        )
        for asset_record in asset_records
    }

    # Build a lookup table of asset keys to last materialization run IDs. We will filter these
    # run IDs out of the "in progress" run lists that are generated below since they have already
    # emitted an output for the run.
    latest_materialization_run_id_by_asset: Dict[AssetKey, Optional[str]] = {
        asset_record.asset_entry.asset_key: (
            asset_record.asset_entry.last_materialization.run_id
            if asset_record.asset_entry.last_materialization
            and asset_record.asset_entry.asset_key in asset_key_set
            else None
        )
        for asset_record in asset_records
    }

    latest_planned_run_ids_by_asset = {
        k: v
        for k, v in {
            asset_record.asset_entry.asset_key: _get_latest_planned_run_id(instance, asset_record)
            for asset_record in asset_records
        }.items()
        if v
    }

    run_records_by_run_id = {}

    run_ids = (
        list(set(latest_planned_run_ids_by_asset.values()))
        if latest_planned_run_ids_by_asset
        else []
    )
    if run_ids:
        run_records = instance.get_run_records(RunsFilter(run_ids=run_ids))
        for run_record in run_records:
            run_records_by_run_id[run_record.dagster_run.run_id] = run_record

    (
        in_progress_run_ids_by_asset,
        unstarted_run_ids_by_asset,
    ) = _get_in_progress_runs_for_assets(
        run_records_by_run_id,
        latest_materialization_run_id_by_asset,
        latest_planned_run_ids_by_asset,
    )

    from .fetch_assets import get_unique_asset_id

    return [
        GrapheneAssetLatestInfo(
            id=get_unique_asset_id(asset_key),
            assetKey=asset_key,
            latestMaterialization=latest_materialization_by_asset.get(asset_key),
            unstartedRunIds=list(unstarted_run_ids_by_asset.get(asset_key, [])),
            inProgressRunIds=list(in_progress_run_ids_by_asset.get(asset_key, [])),
            latestRun=(
                GrapheneRun(run_records_by_run_id[latest_planned_run_ids_by_asset[asset_key]])
                # Dagster UI error occurs if a run is terminated at the same time that this endpoint is
                # called so we check to make sure the run ID exists in the run records.
                if asset_key in latest_planned_run_ids_by_asset
                and latest_planned_run_ids_by_asset[asset_key] in run_records_by_run_id
                else None
            ),
        )
        for asset_key in asset_keys
    ]


def _get_in_progress_runs_for_assets(
    run_records_by_run_id: Mapping[str, RunRecord],
    latest_materialization_run_id_by_asset: Dict[AssetKey, Optional[str]],
    latest_run_ids_by_asset: Dict[AssetKey, str],
) -> Tuple[Mapping[AssetKey, AbstractSet[str]], Mapping[AssetKey, AbstractSet[str]]]:
    in_progress_run_ids_by_asset = defaultdict(set)
    unstarted_run_ids_by_asset = defaultdict(set)

    for asset_key, run_id in latest_run_ids_by_asset.items():
        record = run_records_by_run_id.get(run_id)

        if not record:
            continue

        run = record.dagster_run
        if (
            run.status not in PENDING_STATUSES
            or latest_materialization_run_id_by_asset.get(asset_key) == run.run_id
        ):
            continue

        if run.status in IN_PROGRESS_STATUSES:
            in_progress_run_ids_by_asset[asset_key].add(record.dagster_run.run_id)
        else:
            unstarted_run_ids_by_asset[asset_key].add(record.dagster_run.run_id)

    return in_progress_run_ids_by_asset, unstarted_run_ids_by_asset


def get_runs_count(graphene_info: "ResolveInfo", filters: Optional[RunsFilter]) -> int:
    return graphene_info.context.instance.get_runs_count(filters)


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
