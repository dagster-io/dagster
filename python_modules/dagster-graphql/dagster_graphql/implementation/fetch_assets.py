import datetime
from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    Dict,
    Iterator,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
    Union,
    cast,
)

from dagster_graphql.implementation.loader import (
    CrossRepoAssetDependedByLoader,
    ProjectedLogicalVersionLoader,
)
from dagster_graphql.schema.util import HasContext

import dagster._seven as seven
from dagster import (
    AssetKey,
    DagsterEventType,
    DagsterInstance,
    EventRecordsFilter,
    MultiPartitionKey,
    MultiPartitionsDefinition,
    PartitionsDefinition,
)
from dagster import _check as check
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.definitions.partition import PartitionsSubset
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.events import ASSET_EVENTS
from dagster._core.host_representation.external import ExternalRepository
from dagster._core.host_representation.external_data import (
    ExternalAssetNode,
    ExternalPartitionDimensionDefinition,
)
from dagster._core.host_representation.repository_location import RepositoryLocation
from dagster._core.storage.partition_status_cache import (
    get_materialized_multipartitions_from_tags,
    update_asset_status_cache_values,
)
from dagster._core.storage.tags import get_dimension_from_partition_tag
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

from .utils import capture_error

if TYPE_CHECKING:
    from ..schema.asset_graph import GrapheneAssetNode
    from ..schema.freshness_policy import GrapheneAssetFreshnessInfo


def _normalize_asset_cursor_str(cursor_string):
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
def get_assets(graphene_info, prefix=None, cursor=None, limit=None):
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
    graphene_info,
) -> Iterator[Tuple[RepositoryLocation, ExternalRepository, ExternalAssetNode]]:
    for location in graphene_info.context.repository_locations:
        for repository in location.get_repositories().values():
            for external_asset_node in repository.get_external_asset_nodes():
                yield location, repository, external_asset_node


def get_asset_node_definition_collisions(graphene_info: HasContext, asset_keys: Sequence[AssetKey]):
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


def get_asset_nodes_by_asset_key(graphene_info) -> Mapping[AssetKey, "GrapheneAssetNode"]:
    """
    If multiple repositories have asset nodes for the same asset key, chooses the asset node that
    has an op.
    """

    from ..schema.asset_graph import GrapheneAssetNode

    depended_by_loader = CrossRepoAssetDependedByLoader(context=graphene_info.context)

    projected_logical_version_loader = ProjectedLogicalVersionLoader(
        instance=graphene_info.context.instance,
        key_to_node_map={node.asset_key: node for _, _, node in asset_node_iter(graphene_info)},
        repositories=unique_repos(repo for _, repo, _ in asset_node_iter(graphene_info)),
    )

    asset_nodes_by_asset_key: Dict[AssetKey, GrapheneAssetNode] = {}
    for repo_loc, repo, external_asset_node in asset_node_iter(graphene_info):
        preexisting_node = asset_nodes_by_asset_key.get(external_asset_node.asset_key)
        if preexisting_node is None or preexisting_node.external_asset_node.is_source:
            asset_nodes_by_asset_key[external_asset_node.asset_key] = GrapheneAssetNode(
                repo_loc,
                repo,
                external_asset_node,
                depended_by_loader=depended_by_loader,
                projected_logical_version_loader=projected_logical_version_loader,
            )

    return asset_nodes_by_asset_key


def get_asset_nodes(graphene_info):
    return get_asset_nodes_by_asset_key(graphene_info).values()


def get_asset_node(graphene_info, asset_key):
    from ..schema.errors import GrapheneAssetNotFoundError

    check.inst_param(asset_key, "asset_key", AssetKey)
    node = get_asset_nodes_by_asset_key(graphene_info).get(asset_key, None)
    if not node:
        return GrapheneAssetNotFoundError(asset_key=asset_key)
    return node


def get_asset(graphene_info, asset_key):
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
    graphene_info,
    asset_key,
    partitions=None,
    limit=None,
    before_timestamp=None,
    after_timestamp=None,
    tags: Optional[Mapping[str, str]] = None,
):
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
    graphene_info,
    asset_key,
    partitions=None,
    limit=None,
    before_timestamp=None,
    after_timestamp=None,
):
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


def get_asset_run_ids(graphene_info, asset_key):
    check.inst_param(asset_key, "asset_key", AssetKey)
    instance = graphene_info.context.instance
    return instance.run_ids_for_asset_key(asset_key)


def get_assets_for_run_id(graphene_info, run_id):
    from ..schema.pipelines.pipeline import GrapheneAsset

    check.str_param(run_id, "run_id")

    records = graphene_info.context.instance.all_logs(run_id, of_type=ASSET_EVENTS)
    asset_keys = set(
        [
            record.dagster_event.asset_key
            for record in records
            if record.is_dagster_event and record.dagster_event.asset_key
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


def get_materialization_status_2d_array(
    partitions_def: MultiPartitionsDefinition,
    materialized_keys: List[MultiPartitionKey],
) -> List[List[bool]]:
    """
    Returns a 2d array of booleans representing the materialization status of each partition.

    The rows represent each partition key of the first dimension, and the columns represent each
    partition key of the second dimension. The dimensions follow the order of partitions definitions
    defined in the MultiPartitionsDefinition, which are sorted alphabetically.

    For example, with partition dimensions ab: [a, b] and xy: [x, y], the 2d array will be:
    [
        [a|x materialized?, a|y materialized?],
        [b|x materialized?, b|y materialized?]
    ]
    """

    materialization_status_by_dimension: Dict[str, Dict[str, bool]] = defaultdict(
        lambda: defaultdict(lambda: False)
    )
    primary_dim, secondary_dim = (
        partitions_def.partitions_defs[0],
        partitions_def.partitions_defs[1],
    )
    for partition_key in materialized_keys:
        keys_by_dim = partition_key.keys_by_dimension
        materialization_status_by_dimension[keys_by_dim[primary_dim.name]][
            keys_by_dim[secondary_dim.name]
        ] = True

    materialization_status_2d_arr: List[List[bool]] = []
    secondary_dim_keys = secondary_dim.partitions_def.get_partition_keys()
    for primary_dim_key in primary_dim.partitions_def.get_partition_keys():
        materialization_status_2d_arr.append(
            [
                materialization_status_by_dimension[primary_dim_key][secondary_dim_key]
                for secondary_dim_key in secondary_dim_keys
            ]
        )
    return materialization_status_2d_arr


def get_single_dimension_materialization_status(
    partitions_def: Optional[PartitionsDefinition],
    materialized_keys: List[str],
) -> List[bool]:
    """
    Returns an an array of booleans following the order of the partition keys. For partition keys
    ["a", "b"], the result would be [True, False] if "a" has been materialized and "b" has not.
    """
    if not partitions_def:
        return []

    materialization_status_by_partition: Dict[str, bool] = defaultdict(lambda: False)
    for partition_key in materialized_keys:
        materialization_status_by_partition[partition_key] = True

    ordered_materialization_counts: List[bool] = []
    for partition_key in partitions_def.get_partition_keys():
        ordered_materialization_counts.append(
            materialization_status_by_partition.get(partition_key, False)
        )
    return ordered_materialization_counts


def get_materialization_status_by_partition(
    instance: DagsterInstance,
    asset_key: AssetKey,
    asset_graph: AssetGraph,
) -> Union[List[bool], List[List[bool]]]:
    """
    Returns the materialization status for each partition key. The materialization status
    is a boolean indicating whether the partition has been materialized: True if materialized,
    False if not.
    """
    from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionKey

    partitions_def = asset_graph.partitions_defs_by_key.get(asset_key)
    if not partitions_def:
        return []

    if instance.can_cache_asset_status_data():
        # When the "cached_status_data" column exists in storage, update the column to contain
        # the latest partition status values
        updated_cache_value = update_asset_status_cache_values(
            instance, asset_graph, asset_key
        ).get(asset_key)
        materialized_subset = (
            updated_cache_value.deserialize_materialized_partition_subsets(partitions_def)
            if updated_cache_value
            else partitions_def.empty_subset()
        )
        materialized_keys = materialized_subset.get_partition_keys()

        if isinstance(partitions_def, MultiPartitionsDefinition):
            return get_materialization_status_2d_array(
                partitions_def, [cast(MultiPartitionKey, key) for key in materialized_keys]
            )
        else:
            return get_single_dimension_materialization_status(
                partitions_def, list(materialized_keys)
            )

    else:
        # If the partition status can't be cached, fetch partition status from storage
        if isinstance(partitions_def, MultiPartitionsDefinition):
            return get_materialization_status_2d_array(
                partitions_def,
                get_materialized_multipartitions_from_tags(instance, asset_key, partitions_def),
            )
        else:
            return get_single_dimension_materialization_status(
                partitions_def,
                [
                    partition_key
                    for partition_key, count in instance.get_materialization_count_by_partition(
                        [asset_key]
                    )[asset_key].items()
                    if count > 0
                ],
            )


def get_freshness_info(
    asset_key: AssetKey,
    freshness_policy: FreshnessPolicy,
    data_time_queryer: CachingInstanceQueryer,
    asset_graph: AssetGraph,
) -> "GrapheneAssetFreshnessInfo":
    from ..schema.freshness_policy import GrapheneAssetFreshnessInfo

    current_time = datetime.datetime.now(tz=datetime.timezone.utc)

    latest_record = data_time_queryer.get_latest_materialization_record(asset_key)
    if latest_record is None:
        return GrapheneAssetFreshnessInfo(
            currentMinutesLate=None,
            latestMaterializationMinutesLate=None,
        )
    latest_materialization_time = datetime.datetime.fromtimestamp(
        latest_record.event_log_entry.timestamp,
        tz=datetime.timezone.utc,
    )

    used_data_times = data_time_queryer.get_used_data_times_for_record(
        asset_graph=asset_graph, record=latest_record
    )

    # in the future, if you have upstream source assets with versioning policies, available data
    # times will be based off of the timestamp of the most recent materializations.
    current_minutes_late = freshness_policy.minutes_late(
        evaluation_time=current_time,
        used_data_times=used_data_times,
        available_data_times={
            # assume materializing an asset at time T will update the data time of that asset to T
            key: current_time
            for key in used_data_times.keys()
        },
    )

    latest_materialization_minutes_late = freshness_policy.minutes_late(
        evaluation_time=latest_materialization_time,
        used_data_times=used_data_times,
        available_data_times={key: latest_materialization_time for key in used_data_times.keys()},
    )

    return GrapheneAssetFreshnessInfo(
        currentMinutesLate=current_minutes_late,
        latestMaterializationMinutesLate=latest_materialization_minutes_late,
    )


def unique_repos(external_repositories):
    repos = []
    used = set()
    for external_repository in external_repositories:
        repo_id = (
            external_repository.handle.location_name,
            external_repository.name,
        )
        if not repo_id in used:
            used.add(repo_id)
            repos.append(external_repository)

    return repos
