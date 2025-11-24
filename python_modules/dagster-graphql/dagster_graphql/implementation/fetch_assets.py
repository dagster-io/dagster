import datetime
from collections import defaultdict
from collections.abc import Sequence
from typing import TYPE_CHECKING, AbstractSet, Optional, Union, cast  # noqa: UP035

import dagster_shared.seven as seven
from dagster import (
    AssetKey,
    DagsterEventType,
    DagsterRun,
    _check as check,
)
from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.definitions.partitions.definition import (
    MultiPartitionsDefinition,
    PartitionsDefinition,
    TimeWindowPartitionsDefinition,
)
from dagster._core.definitions.partitions.subset import PartitionsSubset, TimeWindowPartitionsSubset
from dagster._core.definitions.partitions.utils.time_window import (
    PartitionRangeStatus,
    fetch_flattened_time_window_ranges,
)
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.event_api import AssetRecordsFilter, EventLogRecord
from dagster._core.events.log import EventLogEntry
from dagster._core.instance import DynamicPartitionsStore
from dagster._core.remote_representation.external import RemoteRepository
from dagster._core.storage.event_log.sql_event_log import get_max_event_records_limit

if TYPE_CHECKING:
    from dagster_graphql.schema.asset_graph import (
        GrapheneAssetNode,
        GrapheneAssetNodeDefinitionCollision,
    )
    from dagster_graphql.schema.errors import GrapheneAssetNotFoundError
    from dagster_graphql.schema.freshness_policy import GrapheneAssetFreshnessInfo
    from dagster_graphql.schema.pipelines.pipeline import (
        GrapheneAsset,
        GrapheneDefaultPartitionStatuses,
        GrapheneMultiPartitionStatuses,
        GrapheneTimePartitionStatuses,
    )
    from dagster_graphql.schema.roots.assets import (
        GrapheneAssetConnection,
        GrapheneAssetRecordConnection,
    )
    from dagster_graphql.schema.util import ResolveInfo


def _normalize_asset_cursor_str(cursor_string: Optional[str]) -> Optional[str]:
    # the cursor for assets is derived from a json serialized string of the path.  Because there are
    # json serialization differences between JS and Python in its treatment of whitespace, we should
    # take extra precaution here and do a deserialization/serialization pass

    if not cursor_string:
        return cursor_string

    try:
        return seven.json.dumps(seven.json.loads(cursor_string))
    except seven.JSONDecodeError:
        return cursor_string


def get_asset_records(
    graphene_info: "ResolveInfo",
    prefix: Optional[Sequence[str]] = None,
    cursor: Optional[str] = None,
    limit: Optional[int] = None,
) -> "GrapheneAssetRecordConnection":
    from dagster_graphql.schema.pipelines.pipeline import GrapheneAssetRecord
    from dagster_graphql.schema.roots.assets import GrapheneAssetRecordConnection

    instance = graphene_info.context.instance

    normalized_cursor_str = _normalize_asset_cursor_str(cursor)
    materialized_assets = sorted(
        # TODO(salazarm): Replace this with `get_asset_records` once that supports pagination arguments.
        instance.get_asset_keys(prefix=prefix, limit=limit, cursor=normalized_cursor_str),
        key=str,
    )

    return GrapheneAssetRecordConnection(
        assets=[
            GrapheneAssetRecord(
                id=asset_key.to_string(),
                key=asset_key,
            )
            for asset_key in materialized_assets
        ],
        cursor=materialized_assets[-1].to_string() if materialized_assets else None,
    )


def get_assets(
    graphene_info: "ResolveInfo",
    prefix: Optional[Sequence[str]] = None,
    cursor: Optional[str] = None,
    limit: Optional[int] = None,
    asset_keys: Optional[Sequence[AssetKey]] = None,
) -> "GrapheneAssetConnection":
    from dagster_graphql.schema.pipelines.pipeline import GrapheneAsset
    from dagster_graphql.schema.roots.assets import GrapheneAssetConnection

    if asset_keys is not None and prefix is not None:
        # To make this resolver handle both asset_keys and prefix, we would need to
        # make get_asset_keys handle a list of asset_keys so that we filter down to the asset keys that
        # have materializations in the db and match the prefix.
        raise DagsterInvariantViolationError(
            "Cannot provide both asset_keys and prefix",
        )

    instance = graphene_info.context.instance

    normalized_cursor_str = _normalize_asset_cursor_str(cursor)
    if asset_keys is None:
        materialized_keys = instance.get_asset_keys(
            prefix=prefix, limit=limit, cursor=normalized_cursor_str
        )

        asset_graph_keys = {
            asset_key
            for asset_key in graphene_info.context.asset_graph.get_all_asset_keys()
            if (
                (not prefix or asset_key.path[: len(prefix)] == prefix)
                and (not normalized_cursor_str or asset_key.to_string() > normalized_cursor_str)
                and (not asset_keys or asset_key in asset_keys)
            )
        }

        merged_asset_keys = sorted(set(materialized_keys).union(asset_graph_keys), key=str)
    else:
        merged_asset_keys = asset_keys

    if limit:
        merged_asset_keys = merged_asset_keys[:limit]

    return GrapheneAssetConnection(
        nodes=[GrapheneAsset(key=asset_key) for asset_key in merged_asset_keys],
        cursor=merged_asset_keys[-1].to_string() if merged_asset_keys else None,
    )


def get_additional_required_keys(
    graphene_info: "ResolveInfo",
    asset_keys: AbstractSet[AssetKey],
) -> list["AssetKey"]:
    asset_nodes = {graphene_info.context.asset_graph.get(asset_key) for asset_key in asset_keys}

    required_asset_keys = set()
    for asset_node in asset_nodes:
        required_asset_keys.update(asset_node.execution_set_asset_keys)

    return list(required_asset_keys - asset_keys)


def get_asset_node_definition_collisions(
    graphene_info: "ResolveInfo", asset_keys: AbstractSet[AssetKey]
) -> list["GrapheneAssetNodeDefinitionCollision"]:
    from dagster_graphql.schema.asset_graph import GrapheneAssetNodeDefinitionCollision
    from dagster_graphql.schema.external import GrapheneRepository

    repos: dict[AssetKey, list[GrapheneRepository]] = defaultdict(list)
    for asset_key in asset_keys:
        remote_asset_node = graphene_info.context.asset_graph.get(asset_key)
        for info in remote_asset_node.repo_scoped_asset_infos:
            asset_node_snap = info.asset_node.asset_node_snap
            is_defined = (
                asset_node_snap.node_definition_name
                or asset_node_snap.graph_name
                or asset_node_snap.op_name
            )
            if not is_defined:
                continue

            repos[asset_node_snap.asset_key].append(GrapheneRepository(info.handle))

    results: list[GrapheneAssetNodeDefinitionCollision] = []
    for asset_key in repos.keys():
        if len(repos[asset_key]) > 1:
            results.append(
                GrapheneAssetNodeDefinitionCollision(
                    assetKey=asset_key, repositories=repos[asset_key]
                )
            )

    return results


def get_asset_node(
    graphene_info: "ResolveInfo", asset_key: AssetKey
) -> Union["GrapheneAssetNode", "GrapheneAssetNotFoundError"]:
    from dagster_graphql.schema.asset_graph import GrapheneAssetNode
    from dagster_graphql.schema.errors import GrapheneAssetNotFoundError

    check.inst_param(asset_key, "asset_key", AssetKey)

    if not graphene_info.context.asset_graph.has(asset_key):
        return GrapheneAssetNotFoundError(asset_key=asset_key)

    remote_node = graphene_info.context.asset_graph.get(asset_key)
    return GrapheneAssetNode(remote_node)


def get_asset(asset_key: AssetKey) -> "GrapheneAsset":
    from dagster_graphql.schema.pipelines.pipeline import GrapheneAsset

    return GrapheneAsset(key=asset_key)


def get_asset_materialization_event_records(
    graphene_info: "ResolveInfo",
    asset_key: AssetKey,
    partitions: Optional[Sequence[str]] = None,
    limit: Optional[int] = None,
    before_timestamp: Optional[float] = None,
    after_timestamp: Optional[float] = None,
    storage_ids: Optional[Sequence[int]] = None,
    cursor: Optional[str] = None,
) -> Sequence[EventLogRecord]:
    check.inst_param(asset_key, "asset_key", AssetKey)
    check.opt_int_param(limit, "limit")
    check.opt_float_param(before_timestamp, "before_timestamp")

    instance = graphene_info.context.instance
    records_filter = AssetRecordsFilter(
        asset_key=asset_key,
        asset_partitions=partitions,
        before_timestamp=before_timestamp,
        after_timestamp=after_timestamp,
        storage_ids=storage_ids,
    )
    if limit is None:
        event_records = []
        while True:
            event_records_result = instance.fetch_materializations(
                records_filter=records_filter,
                cursor=cursor,
                limit=get_max_event_records_limit(),
            )
            cursor = event_records_result.cursor
            event_records.extend(event_records_result.records)
            if not event_records_result.has_more:
                break
    else:
        event_records = instance.fetch_materializations(
            records_filter=records_filter, limit=limit, cursor=cursor
        ).records

    return event_records


def get_asset_materializations(
    graphene_info: "ResolveInfo",
    asset_key: AssetKey,
    partitions: Optional[Sequence[str]] = None,
    limit: Optional[int] = None,
    before_timestamp: Optional[float] = None,
    after_timestamp: Optional[float] = None,
    storage_ids: Optional[Sequence[int]] = None,
) -> Sequence[EventLogEntry]:
    return [
        event_record.event_log_entry
        for event_record in get_asset_materialization_event_records(
            graphene_info,
            asset_key,
            partitions,
            limit,
            before_timestamp,
            after_timestamp,
            storage_ids,
        )
    ]


def get_asset_failed_to_materialize_event_records(
    graphene_info: "ResolveInfo",
    asset_key: AssetKey,
    partitions: Optional[Sequence[str]] = None,
    limit: Optional[int] = None,
    before_timestamp: Optional[float] = None,
    after_timestamp: Optional[float] = None,
    storage_ids: Optional[Sequence[int]] = None,
    cursor: Optional[str] = None,
) -> Sequence[EventLogRecord]:
    check.inst_param(asset_key, "asset_key", AssetKey)
    check.opt_int_param(limit, "limit")
    check.opt_float_param(before_timestamp, "before_timestamp")

    instance = graphene_info.context.instance
    records_filter = AssetRecordsFilter(
        asset_key=asset_key,
        asset_partitions=partitions,
        before_timestamp=before_timestamp,
        after_timestamp=after_timestamp,
        storage_ids=storage_ids,
    )
    if limit is None:
        event_records = []
        while True:
            event_records_result = instance.fetch_failed_materializations(
                records_filter=records_filter, limit=get_max_event_records_limit(), cursor=cursor
            )
            cursor = event_records_result.cursor
            event_records.extend(event_records_result.records)
            if not event_records_result.has_more:
                break
    else:
        event_records = instance.fetch_failed_materializations(
            records_filter=records_filter, limit=limit, cursor=cursor
        ).records

    return event_records


def get_asset_observation_event_records(
    graphene_info: "ResolveInfo",
    asset_key: AssetKey,
    partitions: Optional[Sequence[str]] = None,
    limit: Optional[int] = None,
    before_timestamp: Optional[float] = None,
    after_timestamp: Optional[float] = None,
    cursor: Optional[str] = None,
) -> Sequence[EventLogRecord]:
    check.inst_param(asset_key, "asset_key", AssetKey)
    check.opt_int_param(limit, "limit")
    check.opt_float_param(before_timestamp, "before_timestamp")
    check.opt_float_param(after_timestamp, "after_timestamp")

    instance = graphene_info.context.instance
    records_filter = AssetRecordsFilter(
        asset_key=asset_key,
        asset_partitions=partitions,
        before_timestamp=before_timestamp,
        after_timestamp=after_timestamp,
    )
    if limit is None:
        event_records = []
        while True:
            event_records_result = instance.fetch_observations(
                records_filter=records_filter,
                cursor=cursor,
                limit=get_max_event_records_limit(),
            )
            cursor = event_records_result.cursor
            event_records.extend(event_records_result.records)
            if not event_records_result.has_more:
                break
    else:
        event_records = instance.fetch_observations(
            records_filter=records_filter, limit=limit, cursor=cursor
        ).records

    return event_records


def get_asset_observations(
    graphene_info: "ResolveInfo",
    asset_key: AssetKey,
    partitions: Optional[Sequence[str]] = None,
    limit: Optional[int] = None,
    before_timestamp: Optional[float] = None,
    after_timestamp: Optional[float] = None,
) -> Sequence[EventLogEntry]:
    event_records = get_asset_observation_event_records(
        graphene_info,
        asset_key,
        partitions,
        limit,
        before_timestamp,
        after_timestamp,
    )
    return [event_record.event_log_entry for event_record in event_records]


def get_assets_for_run(graphene_info: "ResolveInfo", run: DagsterRun) -> Sequence["GrapheneAsset"]:
    from dagster_graphql.schema.pipelines.pipeline import GrapheneAsset

    run_id = run.run_id

    # Fetch observations and materialization events from run
    event_log_records = [
        *graphene_info.context.instance.get_records_for_run(
            run_id,
            of_type=DagsterEventType.ASSET_MATERIALIZATION,
        ).records,
        *graphene_info.context.instance.get_records_for_run(
            run_id,
            of_type=DagsterEventType.ASSET_OBSERVATION,
        ).records,
    ]

    asset_keys = {
        record.event_log_entry.dagster_event.asset_key
        for record in event_log_records
        if record.event_log_entry.dagster_event
    }

    # Fetch planned asset keys from execution plan snapshot
    if run.execution_plan_snapshot_id:
        execution_plan_snapshot = check.not_none(
            graphene_info.context.instance.get_execution_plan_snapshot(
                run.execution_plan_snapshot_id
            )
        )
        asset_keys.update(execution_plan_snapshot.asset_selection)

    return [GrapheneAsset(key=asset_key) for asset_key in asset_keys if asset_key]


def get_unique_asset_id(
    asset_key: AssetKey,
    repository_location_name: Optional[str] = None,
    repository_name: Optional[str] = None,
) -> str:
    repository_identifier = (
        f"{repository_location_name}.{repository_name}"
        if repository_location_name and repository_name
        else ""
    )
    return (
        f"{repository_identifier}.{asset_key.to_string()}"
        if repository_identifier
        else f"{asset_key.to_string()}"
    )


def build_partition_statuses(
    dynamic_partitions_store: DynamicPartitionsStore,
    materialized_partitions_subset: Optional[PartitionsSubset],
    failed_partitions_subset: Optional[PartitionsSubset],
    in_progress_partitions_subset: Optional[PartitionsSubset],
    partitions_def: Optional[PartitionsDefinition],
) -> Union[
    "GrapheneTimePartitionStatuses",
    "GrapheneDefaultPartitionStatuses",
    "GrapheneMultiPartitionStatuses",
]:
    from dagster_graphql.schema.pipelines.pipeline import (
        GrapheneDefaultPartitionStatuses,
        GrapheneTimePartitionRangeStatus,
        GrapheneTimePartitionStatuses,
    )

    if (
        materialized_partitions_subset is None
        and failed_partitions_subset is None
        and in_progress_partitions_subset is None
    ):
        return GrapheneDefaultPartitionStatuses(
            materializedPartitions=[],
            failedPartitions=[],
            unmaterializedPartitions=[],
            materializingPartitions=[],
        )

    materialized_partitions_subset = check.not_none(materialized_partitions_subset)
    failed_partitions_subset = check.not_none(failed_partitions_subset)
    in_progress_partitions_subset = check.not_none(in_progress_partitions_subset)
    check.invariant(
        type(materialized_partitions_subset)
        == type(failed_partitions_subset)
        == type(in_progress_partitions_subset),
        "Expected materialized_partitions_subset, failed_partitions_subset, and"
        " in_progress_partitions_subset to be of the same type",
    )

    if isinstance(materialized_partitions_subset, TimeWindowPartitionsSubset):
        ranges = fetch_flattened_time_window_ranges(
            {
                PartitionRangeStatus.MATERIALIZED: materialized_partitions_subset,
                PartitionRangeStatus.FAILED: cast(
                    "TimeWindowPartitionsSubset", failed_partitions_subset
                ),
                PartitionRangeStatus.MATERIALIZING: cast(
                    "TimeWindowPartitionsSubset", in_progress_partitions_subset
                ),
            },
        )
        graphene_ranges = []
        for r in ranges:
            partition_key_range = cast(
                "TimeWindowPartitionsDefinition",
                materialized_partitions_subset.partitions_def,
            ).get_partition_key_range_for_time_window(r.time_window)
            graphene_ranges.append(
                GrapheneTimePartitionRangeStatus(
                    startTime=r.time_window.start.timestamp(),
                    endTime=r.time_window.end.timestamp(),
                    startKey=partition_key_range.start,
                    endKey=partition_key_range.end,
                    status=r.status,
                )
            )
        return GrapheneTimePartitionStatuses(ranges=graphene_ranges)
    elif isinstance(partitions_def, MultiPartitionsDefinition):
        return get_2d_run_length_encoded_partitions(
            dynamic_partitions_store,
            materialized_partitions_subset,
            failed_partitions_subset,
            in_progress_partitions_subset,
            partitions_def,
        )
    elif partitions_def:
        with partition_loading_context(
            dynamic_partitions_store=dynamic_partitions_store,
        ):
            materialized_keys = materialized_partitions_subset.get_partition_keys()
            failed_keys = failed_partitions_subset.get_partition_keys()
            in_progress_keys = in_progress_partitions_subset.get_partition_keys()

            return GrapheneDefaultPartitionStatuses(
                materializedPartitions=sorted(
                    set(materialized_keys) - set(failed_keys) - set(in_progress_keys)
                ),
                failedPartitions=failed_keys,
                unmaterializedPartitions=materialized_partitions_subset.get_partition_keys_not_in_subset(
                    partitions_def=partitions_def
                ),
                materializingPartitions=in_progress_keys,
            )
    else:
        check.failed("Should not reach this point")


def get_2d_run_length_encoded_partitions(
    dynamic_partitions_store: DynamicPartitionsStore,
    materialized_partitions_subset: PartitionsSubset,
    failed_partitions_subset: PartitionsSubset,
    in_progress_partitions_subset: PartitionsSubset,
    partitions_def: MultiPartitionsDefinition,
) -> "GrapheneMultiPartitionStatuses":
    from dagster_graphql.schema.pipelines.pipeline import (
        GrapheneMultiPartitionRangeStatuses,
        GrapheneMultiPartitionStatuses,
    )

    check.invariant(
        isinstance(partitions_def, MultiPartitionsDefinition),
        "Partitions definition should be multipartitioned",
    )

    with partition_loading_context(
        dynamic_partitions_store=dynamic_partitions_store,
    ):
        primary_dim = partitions_def.primary_dimension
        secondary_dim = partitions_def.secondary_dimension

        dim2_materialized_partition_keys_by_dim1 = defaultdict(set)

        for partition_key in materialized_partitions_subset.get_partition_keys():
            multipartition_key = partitions_def.get_partition_key_from_str(partition_key)
            dim2_materialized_partition_keys_by_dim1[
                multipartition_key.keys_by_dimension[primary_dim.name]
            ].add(multipartition_key.keys_by_dimension[secondary_dim.name])

        dim2_materialized_partition_subset_by_dim1 = {
            key: secondary_dim.partitions_def.empty_subset().with_partition_keys(keys)
            for key, keys in dim2_materialized_partition_keys_by_dim1.items()
        }

        dim2_failed_partition_keys_by_dim1 = defaultdict(set)

        for partition_key in failed_partitions_subset.get_partition_keys():
            multipartition_key = partitions_def.get_partition_key_from_str(partition_key)
            dim2_failed_partition_keys_by_dim1[
                multipartition_key.keys_by_dimension[primary_dim.name]
            ].add(multipartition_key.keys_by_dimension[secondary_dim.name])

        dim2_failed_partition_subset_by_dim1 = {
            key: secondary_dim.partitions_def.empty_subset().with_partition_keys(keys)
            for key, keys in dim2_failed_partition_keys_by_dim1.items()
        }

        dim2_in_progress_partition_keys_by_dim1 = defaultdict(set)

        for partition_key in in_progress_partitions_subset.get_partition_keys():
            multipartition_key = partitions_def.get_partition_key_from_str(partition_key)
            dim2_in_progress_partition_keys_by_dim1[
                multipartition_key.keys_by_dimension[primary_dim.name]
            ].add(multipartition_key.keys_by_dimension[secondary_dim.name])

        dim2_in_progress_partition_subset_by_dim1 = {
            key: secondary_dim.partitions_def.empty_subset().with_partition_keys(keys)
            for key, keys in dim2_in_progress_partition_keys_by_dim1.items()
        }

        materialized_2d_ranges = []

        dim1_keys = primary_dim.partitions_def.get_partition_keys()
        unevaluated_idx = 0
        range_start_idx = 0  # pointer to first dim1 partition with same dim2 materialization status

        if len(dim1_keys) == 0 or len(secondary_dim.partitions_def.get_partition_keys()) == 0:
            return GrapheneMultiPartitionStatuses(ranges=[], primaryDimensionName=primary_dim.name)

        empty_dim2_subset = secondary_dim.partitions_def.empty_subset()

        while unevaluated_idx <= len(dim1_keys):
            if (
                unevaluated_idx == len(dim1_keys)
                or dim2_materialized_partition_keys_by_dim1[dim1_keys[unevaluated_idx]]
                != dim2_materialized_partition_keys_by_dim1[dim1_keys[range_start_idx]]
                or dim2_failed_partition_keys_by_dim1[dim1_keys[unevaluated_idx]]
                != dim2_failed_partition_keys_by_dim1[dim1_keys[range_start_idx]]
                or dim2_in_progress_partition_keys_by_dim1[dim1_keys[unevaluated_idx]]
                != dim2_in_progress_partition_keys_by_dim1[dim1_keys[range_start_idx]]
            ):
                # Add new multipartition range if we've reached the end of the dim1 keys or if the
                # second dimension subsets are different than for the previous dim1 key
                if (
                    len(dim2_materialized_partition_keys_by_dim1[dim1_keys[range_start_idx]]) > 0
                    or len(dim2_failed_partition_keys_by_dim1[dim1_keys[range_start_idx]]) > 0
                    or len(dim2_in_progress_partition_keys_by_dim1[dim1_keys[range_start_idx]]) > 0
                ):
                    # Do not add to materialized_2d_ranges if the dim2 partition subset is empty
                    start_key = dim1_keys[range_start_idx]
                    end_key = dim1_keys[unevaluated_idx - 1]

                    primary_partitions_def = primary_dim.partitions_def
                    if isinstance(primary_partitions_def, TimeWindowPartitionsDefinition):
                        time_windows = cast(
                            "TimeWindowPartitionsDefinition", primary_partitions_def
                        ).time_windows_for_partition_keys(
                            frozenset([start_key, end_key]),
                            validate=False,  # we already know these keys are in the partition set
                        )
                        start_time = time_windows[0].start.timestamp()
                        end_time = time_windows[-1].end.timestamp()
                    else:
                        start_time = None
                        end_time = None

                    materialized_2d_ranges.append(
                        GrapheneMultiPartitionRangeStatuses(
                            primaryDimStartKey=start_key,
                            primaryDimEndKey=end_key,
                            primaryDimStartTime=start_time,
                            primaryDimEndTime=end_time,
                            secondaryDim=build_partition_statuses(
                                dynamic_partitions_store,
                                dim2_materialized_partition_subset_by_dim1.get(
                                    start_key, empty_dim2_subset
                                ),
                                dim2_failed_partition_subset_by_dim1.get(
                                    start_key, empty_dim2_subset
                                ),
                                dim2_in_progress_partition_subset_by_dim1.get(
                                    start_key, empty_dim2_subset
                                ),
                                secondary_dim.partitions_def,
                            ),
                        )
                    )
                range_start_idx = unevaluated_idx
            unevaluated_idx += 1

        return GrapheneMultiPartitionStatuses(
            ranges=materialized_2d_ranges, primaryDimensionName=primary_dim.name
        )


def get_freshness_info(
    asset_key: AssetKey,
    data_time_resolver: CachingDataTimeResolver,
) -> "GrapheneAssetFreshnessInfo":
    from dagster_graphql.schema.freshness_policy import GrapheneAssetFreshnessInfo

    current_time = datetime.datetime.now(tz=datetime.timezone.utc)
    result = data_time_resolver.get_minutes_overdue(asset_key, evaluation_time=current_time)
    return GrapheneAssetFreshnessInfo(
        currentLagMinutes=result.lag_minutes if result else None,
        currentMinutesLate=result.overdue_minutes if result else None,
        latestMaterializationMinutesLate=None,
    )


def unique_repos(
    remote_repositories: Sequence[RemoteRepository],
) -> Sequence[RemoteRepository]:
    repos = []
    used = set()
    for remote_repository in remote_repositories:
        repo_id = (
            remote_repository.handle.location_name,
            remote_repository.name,
        )
        if repo_id not in used:
            used.add(repo_id)
            repos.append(remote_repository)

    return repos
