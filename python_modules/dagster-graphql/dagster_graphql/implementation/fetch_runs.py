import datetime
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, AbstractSet, Any, Optional, Union  # noqa: UP035

from dagster import (
    AssetKey,
    _check as check,
)
from dagster._core.definitions.selector import JobSubsetSelector
from dagster._core.errors import DagsterInvariantViolationError, DagsterRunNotFoundError
from dagster._core.execution.backfill import BulkActionsFilter, BulkActionStatus
from dagster._core.instance import DagsterInstance
from dagster._core.storage.dagster_run import DagsterRunStatus, RunRecord, RunsFilter
from dagster._core.storage.event_log.base import AssetRecord
from dagster._core.storage.tags import BACKFILL_ID_TAG, TagType, get_tag_type
from dagster._record import copy, record
from dagster._time import datetime_from_timestamp
from dagster._utils.warnings import disable_dagster_warnings

from dagster_graphql.implementation.external import ensure_valid_config, get_remote_job_or_raise

if TYPE_CHECKING:
    from dagster_graphql.schema.asset_graph import GrapheneAssetLatestInfo
    from dagster_graphql.schema.errors import GrapheneRunNotFoundError
    from dagster_graphql.schema.execution import GrapheneExecutionPlan
    from dagster_graphql.schema.logs.events import GrapheneRunStepStats
    from dagster_graphql.schema.pipelines.config import GraphenePipelineConfigValidationValid
    from dagster_graphql.schema.pipelines.pipeline import GrapheneEventConnection, GrapheneRun
    from dagster_graphql.schema.pipelines.pipeline_run_stats import GrapheneRunStatsSnapshot
    from dagster_graphql.schema.runs import GrapheneRunGroup, GrapheneRunTagKeys, GrapheneRunTags
    from dagster_graphql.schema.runs_feed import GrapheneRunsFeedConnection, GrapheneRunsFeedView
    from dagster_graphql.schema.util import ResolveInfo


_DELIMITER = "::"


async def gen_run_by_id(
    graphene_info: "ResolveInfo", run_id: str
) -> Union["GrapheneRun", "GrapheneRunNotFoundError"]:
    from dagster_graphql.schema.errors import GrapheneRunNotFoundError
    from dagster_graphql.schema.pipelines.pipeline import GrapheneRun

    record = await RunRecord.gen(graphene_info.context, run_id)
    if not record:
        return GrapheneRunNotFoundError(run_id)
    else:
        return GrapheneRun(record)


def get_run_tag_keys(graphene_info: "ResolveInfo") -> "GrapheneRunTagKeys":
    from dagster_graphql.schema.runs import GrapheneRunTagKeys

    return GrapheneRunTagKeys(
        keys=[
            tag_key
            for tag_key in graphene_info.context.instance.get_run_tag_keys()
            if get_tag_type(tag_key) != TagType.HIDDEN
        ]
    )


def get_run_tags(
    graphene_info: "ResolveInfo",
    tag_keys: list[str],
    value_prefix: Optional[str] = None,
    limit: Optional[int] = None,
) -> "GrapheneRunTags":
    from dagster_graphql.schema.runs import GrapheneRunTags
    from dagster_graphql.schema.tags import GraphenePipelineTagAndValues

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
    from dagster_graphql.schema.errors import GrapheneRunGroupNotFoundError
    from dagster_graphql.schema.pipelines.pipeline import GrapheneRun
    from dagster_graphql.schema.runs import GrapheneRunGroup

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
    from dagster_graphql.schema.pipelines.pipeline import GrapheneRun

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
    if instance.event_log_storage.asset_records_have_last_planned_and_failed_materializations:
        return asset_record.asset_entry.last_planned_materialization_run_id
    else:
        planned_info = instance.get_latest_planned_materialization_info(
            asset_record.asset_entry.asset_key
        )
        return planned_info.run_id if planned_info else None


def get_assets_latest_info(
    graphene_info: "ResolveInfo", step_keys_by_asset: Mapping[AssetKey, Sequence[str]]
) -> Sequence["GrapheneAssetLatestInfo"]:
    from dagster_graphql.schema.asset_graph import GrapheneAssetLatestInfo
    from dagster_graphql.schema.logs.events import GrapheneMaterializationEvent
    from dagster_graphql.schema.pipelines.pipeline import GrapheneRun

    instance = graphene_info.context.instance

    asset_keys = list(step_keys_by_asset.keys())

    if not asset_keys:
        return []

    asset_nodes = {
        asset_key: graphene_info.context.asset_graph.get(asset_key) for asset_key in asset_keys
    }

    asset_records = AssetRecord.blocking_get_many(graphene_info.context, asset_keys)

    latest_materialization_by_asset = {
        asset_record.asset_entry.asset_key: (
            GrapheneMaterializationEvent(event=asset_record.asset_entry.last_materialization)
            if asset_record.asset_entry.last_materialization
            and asset_record.asset_entry.asset_key in step_keys_by_asset
            else None
        )
        for asset_record in asset_records
    }

    # Build a lookup table of asset keys to last materialization run IDs. We will filter these
    # run IDs out of the "in progress" run lists that are generated below since they have already
    # emitted an output for the run.
    latest_materialization_run_id_by_asset: dict[AssetKey, Optional[str]] = {
        asset_record.asset_entry.asset_key: (
            asset_record.asset_entry.last_materialization.run_id
            if asset_record.asset_entry.last_materialization
            and asset_record.asset_entry.asset_key in step_keys_by_asset
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

    from dagster_graphql.implementation.fetch_assets import get_unique_asset_id

    latest_infos = []
    for asset_key in step_keys_by_asset.keys():
        asset_node = asset_nodes[asset_key]
        if asset_node:
            handle = asset_node.resolve_to_singular_repo_scoped_node().repository_handle
            node_id = get_unique_asset_id(
                asset_key,
                handle.repository_name,
                handle.location_name,
            )
        else:
            node_id = get_unique_asset_id(asset_key)

        latest_infos.append(
            GrapheneAssetLatestInfo(
                id=node_id,
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
        )

    return latest_infos


def _get_in_progress_runs_for_assets(
    run_records_by_run_id: Mapping[str, RunRecord],
    latest_materialization_run_id_by_asset: dict[AssetKey, Optional[str]],
    latest_run_ids_by_asset: dict[AssetKey, str],
) -> tuple[Mapping[AssetKey, AbstractSet[str]], Mapping[AssetKey, AbstractSet[str]]]:
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
    from dagster_graphql.schema.pipelines.config import GraphenePipelineConfigValidationValid

    check.inst_param(selector, "selector", JobSubsetSelector)

    remote_job = get_remote_job_or_raise(graphene_info, selector)
    ensure_valid_config(remote_job, run_config)
    return GraphenePipelineConfigValidationValid(pipeline_name=remote_job.name)


def get_execution_plan(
    graphene_info: "ResolveInfo",
    selector: JobSubsetSelector,
    run_config: Mapping[str, Any],
) -> "GrapheneExecutionPlan":
    from dagster_graphql.schema.execution import GrapheneExecutionPlan

    check.inst_param(selector, "selector", JobSubsetSelector)

    remote_job = get_remote_job_or_raise(graphene_info, selector)
    ensure_valid_config(remote_job, run_config)
    return GrapheneExecutionPlan(
        graphene_info.context.get_execution_plan(
            remote_job=remote_job,
            run_config=run_config,
            step_keys_to_execute=None,
            known_state=None,
        )
    )


def get_stats(graphene_info: "ResolveInfo", run_id: str) -> "GrapheneRunStatsSnapshot":
    from dagster_graphql.schema.pipelines.pipeline_run_stats import GrapheneRunStatsSnapshot

    stats = graphene_info.context.instance.get_run_stats(run_id)
    stats.id = "stats-{run_id}"  # type: ignore  # (unused code path)
    return GrapheneRunStatsSnapshot(stats)


def get_step_stats(
    graphene_info: "ResolveInfo", run_id: str, step_keys: Optional[Sequence[str]] = None
) -> Sequence["GrapheneRunStepStats"]:
    from dagster_graphql.schema.logs.events import GrapheneRunStepStats

    step_stats = graphene_info.context.instance.get_run_step_stats(run_id, step_keys)
    return [GrapheneRunStepStats(stats) for stats in step_stats]


def get_logs_for_run(
    graphene_info: "ResolveInfo",
    run_id: str,
    cursor: Optional[str] = None,
    limit: Optional[int] = None,
) -> Union["GrapheneRunNotFoundError", "GrapheneEventConnection"]:
    from dagster_graphql.implementation.events import from_event_record
    from dagster_graphql.schema.errors import GrapheneRunNotFoundError
    from dagster_graphql.schema.pipelines.pipeline import GrapheneEventConnection

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


@record
class RunsFeedCursor:
    """Three part cursor for paginating the Runs Feed. The run_cursor is the run_id of the oldest run that
    has been returned. The backfill_cursor is the id of the oldest backfill that has been returned. The
    timestamp is the timestamp of the oldest entry (run or backfill).

    If the run/backfill cursor is None, that means that no runs/backfills have been returned yet and querying
    should begin at the start of the table. Once all runs/backfills in the table have been returned, the
    corresponding cursor should still be set to the id of the last run/backfill returned.

    The timestamp is used for the following case. If a deployment has 20 runs and 0 backfills, and a query is
    made for 10 Runs Feed entries, the first 10 runs will be returned. At this time, the run_cursor will be an id,
    and the backfill_cursor will be None. Then a backfill is created. If a second query is made for 10 Runs Feed entries
    the newly created backfill will get included in the list, even though it should be included on the first page by time
    order. To prevent this, the timestamp is used to ensure that all returned entires are older than the entries on the
    previous page.
    """

    run_cursor: Optional[str]
    backfill_cursor: Optional[str]
    timestamp: Optional[float]

    def to_string(self) -> str:
        return f"{self.run_cursor if self.run_cursor else ''}{_DELIMITER}{self.backfill_cursor if self.backfill_cursor else ''}{_DELIMITER}{self.timestamp if self.timestamp else ''}"

    @staticmethod
    def from_string(serialized: Optional[str]):
        if serialized is None:
            return RunsFeedCursor(
                run_cursor=None,
                backfill_cursor=None,
                timestamp=None,
            )
        parts = serialized.split(_DELIMITER)
        if len(parts) != 3:
            raise DagsterInvariantViolationError(f"Invalid cursor for querying runs: {serialized}")

        return RunsFeedCursor(
            run_cursor=parts[0] if parts[0] else None,
            backfill_cursor=parts[1] if parts[1] else None,
            timestamp=float(parts[2]) if parts[2] else None,
        )


def _fetch_runs_not_in_backfill(
    instance: DagsterInstance,
    cursor: Optional[str],
    limit: int,
    filters: Optional[RunsFilter],
) -> Sequence[RunRecord]:
    """Fetches limit RunRecords that are not part of a backfill and were created before a given timestamp."""
    runs = []
    while len(runs) < limit:
        # fetch runs in a loop and discard runs that are part of a backfill until we have
        # limit runs to return or have reached the end of the runs table
        new_runs = instance.get_run_records(limit=limit, cursor=cursor, filters=filters)
        if len(new_runs) == 0:
            return runs
        cursor = new_runs[-1].dagster_run.run_id
        runs.extend([run for run in new_runs if run.dagster_run.tags.get(BACKFILL_ID_TAG) is None])

    return runs[:limit]


RUN_STATUS_TO_BULK_ACTION_STATUSES = {
    DagsterRunStatus.SUCCESS: [BulkActionStatus.COMPLETED_SUCCESS],
    DagsterRunStatus.FAILURE: [BulkActionStatus.FAILED, BulkActionStatus.COMPLETED_FAILED],
    DagsterRunStatus.CANCELED: [BulkActionStatus.CANCELED],
    DagsterRunStatus.CANCELING: [BulkActionStatus.CANCELING],
    DagsterRunStatus.STARTED: [BulkActionStatus.REQUESTED],
}


def _bulk_action_statuses_from_run_statuses(
    statuses: Sequence[DagsterRunStatus],
) -> Sequence[BulkActionStatus]:
    full_list = []
    for status in statuses:
        full_list.extend(RUN_STATUS_TO_BULK_ACTION_STATUSES.get(status, []))

    return full_list


def _filters_apply_to_backfills(filters: RunsFilter) -> bool:
    # the following filters do not apply to backfills, so skip fetching backfills if they are set
    if (
        (filters.run_ids is not None and len(filters.run_ids) > 0)
        or filters.updated_after is not None
        or filters.updated_before is not None
        or filters.snapshot_id is not None
    ):
        return False
    # if filtering by statuses and all are not valid backfill statuses, skip fetching backfills
    if filters.statuses and len(_bulk_action_statuses_from_run_statuses(filters.statuses)) == 0:
        return False

    return True


def _bulk_action_filters_from_run_filters(filters: RunsFilter) -> BulkActionsFilter:
    converted_statuses = (
        _bulk_action_statuses_from_run_statuses(filters.statuses) if filters.statuses else None
    )
    backfill_ids = None
    if filters.tags.get(BACKFILL_ID_TAG) is not None:
        backfill_ids = filters.tags[BACKFILL_ID_TAG]
        if isinstance(backfill_ids, str):
            backfill_ids = [backfill_ids]

    tags = (
        {key: value for key, value in filters.tags.items() if key != BACKFILL_ID_TAG}
        if filters.tags
        else None
    )
    return BulkActionsFilter(
        created_before=filters.created_before,
        created_after=filters.created_after,
        statuses=converted_statuses,
        job_name=filters.job_name,
        tags=tags,
        backfill_ids=backfill_ids,
    )


def _replace_created_before_with_cursor(
    filters: RunsFilter, created_before_cursor: Optional[datetime.datetime]
):
    """After the first page of results is returned, created_before_cursor will be less than
    filters.created_before. For pagination of results to work, we need to ensure that the
    created_before filter is set to the minimum of created_before_cursor and filters.created_before.
    """
    if filters.created_before and created_before_cursor:
        created_before = min(created_before_cursor, filters.created_before)
    elif created_before_cursor:
        created_before = created_before_cursor
    elif filters.created_before:
        created_before = filters.created_before
    else:  # no created_before should be applied, return filters as is
        return filters

    return copy(filters, created_before=created_before)


def get_runs_feed_entries(
    graphene_info: "ResolveInfo",
    limit: int,
    filters: Optional[RunsFilter],
    view: "GrapheneRunsFeedView",
    cursor: Optional[str] = None,
) -> "GrapheneRunsFeedConnection":
    """Returns a GrapheneRunsFeedConnection, which contains a merged list of backfills and
    single runs (runs that are not part of a backfill), the cursor to fetch the next page,
    and a boolean indicating if there are more results to fetch.

    Args:
        limit (int): max number of results to return
        cursor (Optional[str]): String that can be deserialized into a RunsFeedCursor. If None, indicates
            that querying should start at the beginning of the table for both runs and backfills.
        filters (Optional[RunsFilter]): Filters to apply to the runs. If None, no filters are applied.
        view (RunsFeedView): If True, include runs that are part of a backfill in the results and exclude backfill objects
    """
    from dagster_graphql.schema.backfill import GraphenePartitionBackfill
    from dagster_graphql.schema.pipelines.pipeline import GrapheneRun
    from dagster_graphql.schema.runs_feed import GrapheneRunsFeedConnection, GrapheneRunsFeedView

    check.opt_str_param(cursor, "cursor")
    check.int_param(limit, "limit")
    check.opt_inst_param(filters, "filters", RunsFilter)

    instance = graphene_info.context.instance
    runs_feed_cursor = RunsFeedCursor.from_string(cursor)
    # In the default "ROOTS" run feed, we exclude runs that are part of backfills. If
    # the user chooses the "RUNS" view, we want to flatten backfills into their runs.
    exclude_subruns = view == GrapheneRunsFeedView.ROOTS

    # if using limit, fetch limit+1 of each type to know if there are more than limit remaining
    fetch_limit = limit + 1
    # filter out any backfills/runs that are newer than the cursor timestamp. See RunsFeedCursor docstring
    # for case when this is necessary
    created_before_cursor = (
        datetime_from_timestamp(runs_feed_cursor.timestamp) if runs_feed_cursor.timestamp else None
    )

    should_fetch_backfills = (
        view == GrapheneRunsFeedView.ROOTS or view == GrapheneRunsFeedView.BACKFILLS
    ) and (_filters_apply_to_backfills(filters) if filters else True)
    if filters:
        check.invariant(
            filters.exclude_subruns is None,
            "filters.exclude_subruns must be None when fetching the runs feed. Use include_runs_from_backfills instead.",
        )
        with disable_dagster_warnings():
            run_filters = copy(filters, exclude_subruns=exclude_subruns)
            run_filters = _replace_created_before_with_cursor(run_filters, created_before_cursor)
        backfill_filters = (
            _bulk_action_filters_from_run_filters(run_filters) if should_fetch_backfills else None
        )
    else:
        with disable_dagster_warnings():
            run_filters = RunsFilter(
                created_before=created_before_cursor, exclude_subruns=exclude_subruns
            )
        backfill_filters = BulkActionsFilter(created_before=created_before_cursor)

    if should_fetch_backfills:
        backfills = [
            GraphenePartitionBackfill(backfill)
            for backfill in instance.get_backfills(
                cursor=runs_feed_cursor.backfill_cursor,
                limit=fetch_limit,
                filters=backfill_filters,
            )
        ]
    else:
        backfills = []

    # if we are not showing runs within backfills and the backfill_id filter is set, we know
    # there will be no results, so we can skip fetching runs
    should_fetch_runs = (
        view == GrapheneRunsFeedView.ROOTS or view == GrapheneRunsFeedView.RUNS
    ) and not (exclude_subruns and run_filters.tags.get(BACKFILL_ID_TAG) is not None)
    if should_fetch_runs:
        runs = [
            GrapheneRun(run)
            for run in instance.get_run_records(
                limit=fetch_limit, cursor=runs_feed_cursor.run_cursor, filters=run_filters
            )
        ]
    else:
        runs = []

    # if we fetched limit+1 of either runs or backfills, we know there must be more results
    # to fetch on the next call since we will return limit results for this call. Additionally,
    # if we fetched more than limit of runs and backfill combined, we know there are more results
    has_more = (
        len(backfills) == fetch_limit
        or len(runs) == fetch_limit
        or len(backfills) + len(runs) > limit
    )

    all_entries = backfills + runs

    # order runs and backfills by create_time. typically we sort by storage id but that won't work here since
    # they are different tables
    all_entries = sorted(
        all_entries,
        key=lambda x: x.creation_timestamp,
        reverse=True,
    )

    to_return = all_entries[:limit]

    new_run_cursor = None
    new_backfill_cursor = None
    for entry in reversed(to_return):
        if new_run_cursor is not None and new_backfill_cursor is not None:
            break
        if new_backfill_cursor is None and isinstance(entry, GraphenePartitionBackfill):
            new_backfill_cursor = entry.id
        if new_run_cursor is None and isinstance(entry, GrapheneRun):
            new_run_cursor = entry.runId

    new_timestamp = to_return[-1].creation_timestamp if to_return else None

    # if either of the new cursors are None, replace with the cursor passed in so the next call doesn't
    # restart at the top the table.
    final_cursor = RunsFeedCursor(
        run_cursor=new_run_cursor if new_run_cursor else runs_feed_cursor.run_cursor,
        backfill_cursor=new_backfill_cursor
        if new_backfill_cursor
        else runs_feed_cursor.backfill_cursor,
        timestamp=new_timestamp if new_timestamp else runs_feed_cursor.timestamp,
    )

    return GrapheneRunsFeedConnection(
        results=to_return, cursor=final_cursor.to_string(), hasMore=has_more
    )


def get_runs_feed_count(
    graphene_info: "ResolveInfo", filters: Optional[RunsFilter], view: "GrapheneRunsFeedView"
) -> int:
    from dagster_graphql.schema.runs_feed import GrapheneRunsFeedView

    # In the default "ROOTS" run feed, we exclude runs that are part of backfills. If
    # the user chooses the "RUNS" view, we want to flatten backfills into their runs.
    exclude_subruns = view == GrapheneRunsFeedView.ROOTS
    should_fetch_runs = view == GrapheneRunsFeedView.RUNS or view == GrapheneRunsFeedView.ROOTS
    should_fetch_backfills = (
        view == GrapheneRunsFeedView.BACKFILLS or view == GrapheneRunsFeedView.ROOTS
    ) and (_filters_apply_to_backfills(filters) if filters else True)
    with disable_dagster_warnings():
        run_filters = (
            copy(filters, exclude_subruns=exclude_subruns)
            if filters
            else RunsFilter(exclude_subruns=exclude_subruns)
        )
    if should_fetch_backfills:
        backfill_filters = _bulk_action_filters_from_run_filters(run_filters)
        backfills_count = graphene_info.context.instance.get_backfills_count(backfill_filters)
    else:
        backfills_count = 0

    if should_fetch_runs:
        runs_count = graphene_info.context.instance.get_runs_count(run_filters)
    else:
        runs_count = 0

    return runs_count + backfills_count
