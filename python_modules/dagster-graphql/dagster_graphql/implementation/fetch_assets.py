from collections import defaultdict
from typing import TYPE_CHECKING, Dict, List, Mapping

from dagster_graphql.implementation.loader import CrossRepoAssetDependedByLoader

import dagster._seven as seven
from dagster import AssetKey, DagsterEventType, EventRecordsFilter
from dagster import _check as check
from dagster._core.events import ASSET_EVENTS

from .utils import capture_error

if TYPE_CHECKING:
    from ..schema.asset_graph import GrapheneAssetNode


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


def asset_node_iter(graphene_info):
    for location in graphene_info.context.repository_locations:
        for repository in location.get_repositories().values():
            for external_asset_node in repository.get_external_asset_nodes():
                yield location, repository, external_asset_node


def get_asset_node_definition_collisions(graphene_info, asset_keys):
    from ..schema.asset_graph import GrapheneAssetNodeDefinitionCollision
    from ..schema.external import GrapheneRepository

    repos: Dict[AssetKey, GrapheneRepository] = defaultdict(list)

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

    asset_nodes_by_asset_key: Dict[AssetKey, GrapheneAssetNode] = {}
    for repo_loc, repo, external_asset_node in asset_node_iter(graphene_info):
        preexisting_node = asset_nodes_by_asset_key.get(external_asset_node.asset_key)
        if preexisting_node is None or preexisting_node.external_asset_node.op_name is None:
            asset_nodes_by_asset_key[external_asset_node.asset_key] = GrapheneAssetNode(
                repo_loc,
                repo,
                external_asset_node,
                depended_by_loader=depended_by_loader,
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
):
    check.inst_param(asset_key, "asset_key", AssetKey)
    check.opt_int_param(limit, "limit")
    check.opt_float_param(before_timestamp, "before_timestamp")
    instance = graphene_info.context.instance
    event_records = instance.get_event_records(
        EventRecordsFilter(
            event_type=DagsterEventType.ASSET_MATERIALIZATION,
            asset_key=asset_key,
            asset_partitions=partitions,
            before_timestamp=before_timestamp,
            after_timestamp=after_timestamp,
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
    asset_key: AssetKey, repository_location_name: str = None, repository_name: str = None
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
