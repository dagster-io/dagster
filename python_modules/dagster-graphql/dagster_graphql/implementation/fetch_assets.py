import datetime
from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Dict,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
    cast,
)

import dagster._seven as seven
from dagster import (
    AssetKey,
    DagsterEventType,
    DagsterInstance,
    EventRecordsFilter,
    MultiPartitionKey,
    MultiPartitionsDefinition,
    _check as check,
)
from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.external_asset_graph import ExternalAssetGraph
from dagster._core.definitions.multi_dimensional_partitions import (
    MultiPartitionsSubset,
)
from dagster._core.definitions.partition import (
    CachingDynamicPartitionsLoader,
    DefaultPartitionsSubset,
    PartitionsDefinition,
    PartitionsSubset,
)
from dagster._core.definitions.time_window_partitions import (
    PartitionRangeStatus,
    TimeWindowPartitionsDefinition,
    TimeWindowPartitionsSubset,
    fetch_flattened_time_window_ranges,
)
from dagster._core.events import ASSET_EVENTS
from dagster._core.events.log import EventLogEntry
from dagster._core.host_representation.code_location import CodeLocation
from dagster._core.host_representation.external import ExternalRepository
from dagster._core.host_representation.external_data import ExternalAssetNode
from dagster._core.instance import DynamicPartitionsStore
from dagster._core.storage.partition_status_cache import (
    build_failed_and_in_progress_partition_subset,
    get_and_update_asset_status_cache_value,
    get_materialized_multipartitions,
    get_validated_partition_keys,
    is_cacheable_partition_type,
)

from dagster_graphql.implementation.loader import (
    CrossRepoAssetDependedByLoader,
    StaleStatusLoader,
)

from .utils import capture_error

if TYPE_CHECKING:
    from ..schema.asset_graph import GrapheneAssetNode, GrapheneAssetNodeDefinitionCollision
    from ..schema.errors import GrapheneAssetNotFoundError
    from ..schema.freshness_policy import GrapheneAssetFreshnessInfo
    from ..schema.pipelines.pipeline import (
        GrapheneAsset,
        GrapheneDefaultPartitions,
        GrapheneMultiPartitions,
        GrapheneTimePartitions,
    )
    from ..schema.roots.assets import GrapheneAssetConnection
    from ..schema.util import ResolveInfo


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


@capture_error
def get_assets(
    graphene_info: "ResolveInfo",
    prefix: Optional[Sequence[str]] = None,
    cursor: Optional[str] = None,
    limit: Optional[int] = None,
) -> "GrapheneAssetConnection":
    from ..schema.pipelines.pipeline import GrapheneAsset
    from ..schema.roots.assets import GrapheneAssetConnection

    instance = graphene_info.context.instance

    normalized_cursor_str = _normalize_asset_cursor_str(cursor)
    materialized_keys = instance.get_asset_keys(
        prefix=prefix, limit=limit, cursor=normalized_cursor_str
    )
    asset_nodes_by_asset_key = {
        asset_key: asset_node
        for asset_key, asset_node in get_asset_nodes_by_asset_key(graphene_info).items()
        if (not prefix or asset_key.path[: len(prefix)] == prefix)
        and (not cursor or asset_key.to_string() > cursor)
    }

    asset_keys = sorted(set(materialized_keys).union(asset_nodes_by_asset_key.keys()), key=str)
    if limit:
        asset_keys = asset_keys[:limit]

    return GrapheneAssetConnection(
        nodes=[
            GrapheneAsset(
                key=asset_key,
                definition=asset_nodes_by_asset_key.get(asset_key),
            )
            for asset_key in asset_keys
        ]
    )


def asset_node_iter(
    graphene_info: "ResolveInfo",
) -> Iterator[Tuple[CodeLocation, ExternalRepository, ExternalAssetNode]]:
    for location in graphene_info.context.code_locations:
        for repository in location.get_repositories().values():
            for external_asset_node in repository.get_external_asset_nodes():
                yield location, repository, external_asset_node


def get_asset_node_definition_collisions(
    graphene_info: "ResolveInfo", asset_keys: AbstractSet[AssetKey]
) -> List["GrapheneAssetNodeDefinitionCollision"]:
    from ..schema.asset_graph import GrapheneAssetNodeDefinitionCollision
    from ..schema.external import GrapheneRepository

    repos: Dict[AssetKey, List[GrapheneRepository]] = defaultdict(list)

    for repo_loc, repo, external_asset_node in asset_node_iter(graphene_info):
        if external_asset_node.asset_key in asset_keys:
            is_defined = (
                external_asset_node.node_definition_name
                or external_asset_node.graph_name
                or external_asset_node.op_name
            )
            if not is_defined:
                continue
            repos[external_asset_node.asset_key].append(
                GrapheneRepository(
                    instance=graphene_info.context.instance,
                    repository=repo,
                    repository_location=repo_loc,
                )
            )

    results: List[GrapheneAssetNodeDefinitionCollision] = []
    for asset_key in repos.keys():
        if len(repos[asset_key]) > 1:
            results.append(
                GrapheneAssetNodeDefinitionCollision(
                    assetKey=asset_key, repositories=repos[asset_key]
                )
            )

    return results


def get_asset_nodes_by_asset_key(
    graphene_info: "ResolveInfo",
) -> Mapping[AssetKey, "GrapheneAssetNode"]:
    """If multiple repositories have asset nodes for the same asset key, chooses the asset node that
    has an op.
    """
    from ..schema.asset_graph import GrapheneAssetNode

    depended_by_loader = CrossRepoAssetDependedByLoader(context=graphene_info.context)

    stale_status_loader = StaleStatusLoader(
        instance=graphene_info.context.instance,
        asset_graph=lambda: ExternalAssetGraph.from_workspace(graphene_info.context),
    )

    dynamic_partitions_loader = CachingDynamicPartitionsLoader(graphene_info.context.instance)

    asset_nodes_by_asset_key: Dict[AssetKey, GrapheneAssetNode] = {}
    for repo_loc, repo, external_asset_node in asset_node_iter(graphene_info):
        preexisting_node = asset_nodes_by_asset_key.get(external_asset_node.asset_key)
        if preexisting_node is None or preexisting_node.external_asset_node.is_source:
            asset_nodes_by_asset_key[external_asset_node.asset_key] = GrapheneAssetNode(
                repo_loc,
                repo,
                external_asset_node,
                depended_by_loader=depended_by_loader,
                stale_status_loader=stale_status_loader,
                dynamic_partitions_loader=dynamic_partitions_loader,
            )

    return asset_nodes_by_asset_key


def get_asset_nodes(graphene_info: "ResolveInfo"):
    return get_asset_nodes_by_asset_key(graphene_info).values()


def get_asset_node(
    graphene_info: "ResolveInfo", asset_key: AssetKey
) -> Union["GrapheneAssetNode", "GrapheneAssetNotFoundError"]:
    from ..schema.errors import GrapheneAssetNotFoundError

    check.inst_param(asset_key, "asset_key", AssetKey)
    node = get_asset_nodes_by_asset_key(graphene_info).get(asset_key, None)
    if not node:
        return GrapheneAssetNotFoundError(asset_key=asset_key)
    return node


def get_asset(
    graphene_info: "ResolveInfo", asset_key: AssetKey
) -> Union["GrapheneAsset", "GrapheneAssetNotFoundError"]:
    from ..schema.errors import GrapheneAssetNotFoundError
    from ..schema.pipelines.pipeline import GrapheneAsset

    check.inst_param(asset_key, "asset_key", AssetKey)
    instance = graphene_info.context.instance

    asset_nodes_by_asset_key = get_asset_nodes_by_asset_key(graphene_info)
    asset_node = asset_nodes_by_asset_key.get(asset_key)

    if not asset_node and not instance.has_asset_key(asset_key):
        return GrapheneAssetNotFoundError(asset_key=asset_key)

    return GrapheneAsset(key=asset_key, definition=asset_node)


def get_asset_materializations(
    graphene_info: "ResolveInfo",
    asset_key: AssetKey,
    partitions: Optional[Sequence[str]] = None,
    limit: Optional[int] = None,
    before_timestamp: Optional[float] = None,
    after_timestamp: Optional[float] = None,
    tags: Optional[Mapping[str, str]] = None,
) -> Sequence[EventLogEntry]:
    check.inst_param(asset_key, "asset_key", AssetKey)
    check.opt_int_param(limit, "limit")
    check.opt_float_param(before_timestamp, "before_timestamp")
    check.opt_mapping_param(tags, "tags", key_type=str, value_type=str)

    instance = graphene_info.context.instance
    event_records = instance.get_event_records(
        EventRecordsFilter(
            event_type=DagsterEventType.ASSET_MATERIALIZATION,
            asset_key=asset_key,
            asset_partitions=partitions,
            before_timestamp=before_timestamp,
            after_timestamp=after_timestamp,
            tags=tags,
        ),
        limit=limit,
    )
    return [event_record.event_log_entry for event_record in event_records]


def get_asset_observations(
    graphene_info: "ResolveInfo",
    asset_key: AssetKey,
    partitions: Optional[Sequence[str]] = None,
    limit: Optional[int] = None,
    before_timestamp: Optional[float] = None,
    after_timestamp: Optional[float] = None,
) -> Sequence[EventLogEntry]:
    check.inst_param(asset_key, "asset_key", AssetKey)
    check.opt_int_param(limit, "limit")
    check.opt_float_param(before_timestamp, "before_timestamp")
    check.opt_float_param(after_timestamp, "after_timestamp")
    instance = graphene_info.context.instance
    event_records = instance.get_event_records(
        EventRecordsFilter(
            event_type=DagsterEventType.ASSET_OBSERVATION,
            asset_key=asset_key,
            asset_partitions=partitions,
            before_timestamp=before_timestamp,
            after_timestamp=after_timestamp,
        ),
        limit=limit,
    )
    return [event_record.event_log_entry for event_record in event_records]


def get_asset_run_ids(graphene_info: "ResolveInfo", asset_key: AssetKey) -> Sequence[str]:
    check.inst_param(asset_key, "asset_key", AssetKey)
    instance = graphene_info.context.instance
    return instance.run_ids_for_asset_key(asset_key)


def get_assets_for_run_id(graphene_info: "ResolveInfo", run_id: str) -> Sequence["GrapheneAsset"]:
    from ..schema.pipelines.pipeline import GrapheneAsset

    check.str_param(run_id, "run_id")

    records = graphene_info.context.instance.all_logs(run_id, of_type=ASSET_EVENTS)
    asset_keys = set(
        [
            record.get_dagster_event().asset_key
            for record in records
            if record.is_dagster_event and record.get_dagster_event().asset_key
        ]
    )
    return [GrapheneAsset(key=asset_key) for asset_key in asset_keys]


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


def get_partition_subsets(
    instance: DagsterInstance,
    asset_key: AssetKey,
    dynamic_partitions_loader: DynamicPartitionsStore,
    partitions_def: Optional[PartitionsDefinition] = None,
) -> Tuple[Optional[PartitionsSubset], Optional[PartitionsSubset], Optional[PartitionsSubset]]:
    """Returns a tuple of PartitionSubset objects: the first is the materialized partitions,
    the second is the failed partitions, and the third are in progress.
    """
    if not partitions_def:
        return None, None, None

    if instance.can_cache_asset_status_data() and is_cacheable_partition_type(partitions_def):
        # When the "cached_status_data" column exists in storage, update the column to contain
        # the latest partition status values
        updated_cache_value = get_and_update_asset_status_cache_value(
            instance, asset_key, partitions_def, dynamic_partitions_loader
        )
        materialized_subset = (
            updated_cache_value.deserialize_materialized_partition_subsets(partitions_def)
            if updated_cache_value
            else partitions_def.empty_subset()
        )
        failed_subset = (
            updated_cache_value.deserialize_failed_partition_subsets(partitions_def)
            if updated_cache_value
            else partitions_def.empty_subset()
        )
        in_progress_subset = (
            updated_cache_value.deserialize_in_progress_partition_subsets(partitions_def)
            if updated_cache_value
            else partitions_def.empty_subset()
        )

        return materialized_subset, failed_subset, in_progress_subset

    else:
        # If the partition status can't be cached, fetch partition status from storage
        if isinstance(partitions_def, MultiPartitionsDefinition):
            materialized_keys = get_materialized_multipartitions(
                instance, asset_key, partitions_def
            )
        else:
            materialized_keys = [
                partition_key
                for partition_key, count in instance.get_materialization_count_by_partition(
                    [asset_key]
                )[asset_key].items()
                if count > 0
            ]

        validated_keys = get_validated_partition_keys(
            dynamic_partitions_loader, partitions_def, set(materialized_keys)
        )

        materialized_subset = (
            partitions_def.empty_subset().with_partition_keys(validated_keys)
            if validated_keys
            else partitions_def.empty_subset()
        )

        failed_subset, in_progress_subset, _ = build_failed_and_in_progress_partition_subset(
            instance, asset_key, partitions_def, dynamic_partitions_loader
        )

        return materialized_subset, failed_subset, in_progress_subset


def build_partition_statuses(
    dynamic_partitions_store: DynamicPartitionsStore,
    materialized_partitions_subset: Optional[PartitionsSubset],
    failed_partitions_subset: Optional[PartitionsSubset],
    in_progress_partitions_subset: Optional[PartitionsSubset],
) -> Union["GrapheneTimePartitions", "GrapheneDefaultPartitions", "GrapheneMultiPartitions"]:
    from ..schema.pipelines.pipeline import (
        GrapheneDefaultPartitions,
        GrapheneTimePartitionRange,
        GrapheneTimePartitions,
    )

    if (
        materialized_partitions_subset is None
        and failed_partitions_subset is None
        and in_progress_partitions_subset is None
    ):
        return GrapheneDefaultPartitions(
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
        (
            "Expected materialized_partitions_subset, failed_partitions_subset, and"
            " in_progress_partitions_subset to be of the same type"
        ),
    )

    if isinstance(materialized_partitions_subset, TimeWindowPartitionsSubset):
        ranges = fetch_flattened_time_window_ranges(
            {
                PartitionRangeStatus.MATERIALIZED: materialized_partitions_subset,
                PartitionRangeStatus.FAILED: cast(
                    TimeWindowPartitionsSubset, failed_partitions_subset
                ),
                PartitionRangeStatus.MATERIALIZING: cast(
                    TimeWindowPartitionsSubset, in_progress_partitions_subset
                ),
            },
        )
        graphene_ranges = []
        for r in ranges:
            partition_key_range = cast(
                TimeWindowPartitionsDefinition, materialized_partitions_subset.partitions_def
            ).get_partition_key_range_for_time_window(r.time_window)
            graphene_ranges.append(
                GrapheneTimePartitionRange(
                    startTime=r.time_window.start.timestamp(),
                    endTime=r.time_window.end.timestamp(),
                    startKey=partition_key_range.start,
                    endKey=partition_key_range.end,
                    status=r.status,
                )
            )
        return GrapheneTimePartitions(ranges=graphene_ranges)
    elif isinstance(materialized_partitions_subset, MultiPartitionsSubset):
        return get_2d_run_length_encoded_partitions(
            dynamic_partitions_store,
            materialized_partitions_subset,
            failed_partitions_subset,
            in_progress_partitions_subset,
        )
    elif isinstance(materialized_partitions_subset, DefaultPartitionsSubset):
        materialized_keys = materialized_partitions_subset.get_partition_keys()
        failed_keys = failed_partitions_subset.get_partition_keys()
        in_progress_keys = in_progress_partitions_subset.get_partition_keys()

        return GrapheneDefaultPartitions(
            materializedPartitions=set(materialized_keys)
            - set(failed_keys)
            - set(in_progress_keys),
            failedPartitions=failed_keys,
            unmaterializedPartitions=materialized_partitions_subset.get_partition_keys_not_in_subset(
                dynamic_partitions_store=dynamic_partitions_store
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
) -> "GrapheneMultiPartitions":
    from ..schema.pipelines.pipeline import (
        GrapheneMultiPartitionRange,
        GrapheneMultiPartitions,
    )

    if (
        not isinstance(materialized_partitions_subset.partitions_def, MultiPartitionsDefinition)
        or not isinstance(failed_partitions_subset.partitions_def, MultiPartitionsDefinition)
        or not isinstance(in_progress_partitions_subset.partitions_def, MultiPartitionsDefinition)
    ):
        check.failed("Can only fetch 2D run length encoded partitions for multipartitioned assets")

    primary_dim = materialized_partitions_subset.partitions_def.primary_dimension
    secondary_dim = materialized_partitions_subset.partitions_def.secondary_dimension

    dim2_materialized_partition_subset_by_dim1: Dict[str, PartitionsSubset] = defaultdict(
        lambda: secondary_dim.partitions_def.empty_subset()
    )
    for partition_key in cast(
        Sequence[MultiPartitionKey], materialized_partitions_subset.get_partition_keys()
    ):
        dim2_materialized_partition_subset_by_dim1[
            partition_key.keys_by_dimension[primary_dim.name]
        ] = dim2_materialized_partition_subset_by_dim1[
            partition_key.keys_by_dimension[primary_dim.name]
        ].with_partition_keys(
            [partition_key.keys_by_dimension[secondary_dim.name]]
        )

    dim2_failed_partition_subset_by_dim1: Dict[str, PartitionsSubset] = defaultdict(
        lambda: secondary_dim.partitions_def.empty_subset()
    )
    for partition_key in cast(
        Sequence[MultiPartitionKey], failed_partitions_subset.get_partition_keys()
    ):
        dim2_failed_partition_subset_by_dim1[
            partition_key.keys_by_dimension[primary_dim.name]
        ] = dim2_failed_partition_subset_by_dim1[
            partition_key.keys_by_dimension[primary_dim.name]
        ].with_partition_keys(
            [partition_key.keys_by_dimension[secondary_dim.name]]
        )

    dim2_in_progress_partition_subset_by_dim1: Dict[str, PartitionsSubset] = defaultdict(
        lambda: secondary_dim.partitions_def.empty_subset()
    )
    for partition_key in cast(
        Sequence[MultiPartitionKey], in_progress_partitions_subset.get_partition_keys()
    ):
        dim2_in_progress_partition_subset_by_dim1[
            partition_key.keys_by_dimension[primary_dim.name]
        ] = dim2_in_progress_partition_subset_by_dim1[
            partition_key.keys_by_dimension[primary_dim.name]
        ].with_partition_keys(
            [partition_key.keys_by_dimension[secondary_dim.name]]
        )

    materialized_2d_ranges = []

    dim1_keys = primary_dim.partitions_def.get_partition_keys(
        dynamic_partitions_store=dynamic_partitions_store
    )
    unevaluated_idx = 0
    range_start_idx = 0  # pointer to first dim1 partition with same dim2 materialization status

    if (
        len(dim1_keys) == 0
        or len(
            secondary_dim.partitions_def.get_partition_keys(
                dynamic_partitions_store=dynamic_partitions_store
            )
        )
        == 0
    ):
        return GrapheneMultiPartitions(ranges=[], primaryDimensionName=primary_dim.name)

    while unevaluated_idx <= len(dim1_keys):
        if (
            unevaluated_idx == len(dim1_keys)
            or dim2_materialized_partition_subset_by_dim1[dim1_keys[unevaluated_idx]]
            != dim2_materialized_partition_subset_by_dim1[dim1_keys[range_start_idx]]
            or dim2_failed_partition_subset_by_dim1[dim1_keys[unevaluated_idx]]
            != dim2_failed_partition_subset_by_dim1[dim1_keys[range_start_idx]]
            or dim2_in_progress_partition_subset_by_dim1[dim1_keys[unevaluated_idx]]
            != dim2_in_progress_partition_subset_by_dim1[dim1_keys[range_start_idx]]
        ):
            # Add new multipartition range if we've reached the end of the dim1 keys or if the
            # second dimension subsets are different than for the previous dim1 key
            if (
                len(dim2_materialized_partition_subset_by_dim1[dim1_keys[range_start_idx]]) > 0
                or len(dim2_failed_partition_subset_by_dim1[dim1_keys[range_start_idx]]) > 0
                or len(dim2_in_progress_partition_subset_by_dim1[dim1_keys[range_start_idx]]) > 0
            ):
                # Do not add to materialized_2d_ranges if the dim2 partition subset is empty
                start_key = dim1_keys[range_start_idx]
                end_key = dim1_keys[unevaluated_idx - 1]

                primary_partitions_def = primary_dim.partitions_def
                if isinstance(primary_partitions_def, TimeWindowPartitionsDefinition):
                    time_windows = cast(
                        TimeWindowPartitionsDefinition, primary_partitions_def
                    ).time_windows_for_partition_keys(list(set([start_key, end_key])))
                    start_time = time_windows[0].start.timestamp()
                    end_time = time_windows[-1].end.timestamp()
                else:
                    start_time = None
                    end_time = None

                materialized_2d_ranges.append(
                    GrapheneMultiPartitionRange(
                        primaryDimStartKey=start_key,
                        primaryDimEndKey=end_key,
                        primaryDimStartTime=start_time,
                        primaryDimEndTime=end_time,
                        secondaryDim=build_partition_statuses(
                            dynamic_partitions_store,
                            dim2_materialized_partition_subset_by_dim1[start_key],
                            dim2_failed_partition_subset_by_dim1[start_key],
                            dim2_in_progress_partition_subset_by_dim1[start_key],
                        ),
                    )
                )
            range_start_idx = unevaluated_idx
        unevaluated_idx += 1

    return GrapheneMultiPartitions(
        ranges=materialized_2d_ranges, primaryDimensionName=primary_dim.name
    )


def get_freshness_info(
    asset_key: AssetKey,
    data_time_resolver: CachingDataTimeResolver,
) -> "GrapheneAssetFreshnessInfo":
    from ..schema.freshness_policy import GrapheneAssetFreshnessInfo

    current_time = datetime.datetime.now(tz=datetime.timezone.utc)

    return GrapheneAssetFreshnessInfo(
        currentMinutesLate=data_time_resolver.get_current_minutes_late(
            asset_key, evaluation_time=current_time
        ),
        latestMaterializationMinutesLate=None,
    )


def unique_repos(
    external_repositories: Sequence[ExternalRepository],
) -> Sequence[ExternalRepository]:
    repos = []
    used = set()
    for external_repository in external_repositories:
        repo_id = (
            external_repository.handle.location_name,
            external_repository.name,
        )
        if repo_id not in used:
            used.add(repo_id)
            repos.append(external_repository)

    return repos
