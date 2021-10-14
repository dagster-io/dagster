from dagster import AssetKey, DagsterEventType, EventRecordsFilter, check, seven

from .utils import capture_error


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
            GrapheneAsset(key=asset_key, definition=asset_nodes_by_asset_key.get(asset_key))
            for asset_key in asset_keys
        ]
    )


def get_asset_nodes_by_asset_key(graphene_info):
    from ..schema.asset_graph import GrapheneAssetNode

    return {
        external_asset_node.asset_key: GrapheneAssetNode(repository, external_asset_node)
        for location in graphene_info.context.repository_locations
        for repository in location.get_repositories().values()
        for external_asset_node in repository.get_external_asset_nodes()
    }


def get_asset_nodes(graphene_info):
    from ..schema.asset_graph import GrapheneAssetNode

    return [
        GrapheneAssetNode(repository, external_asset_node)
        for location in graphene_info.context.repository_locations
        for repository in location.get_repositories().values()
        for external_asset_node in repository.get_external_asset_nodes()
    ]


def get_asset_node(graphene_info, asset_key):
    from ..schema.errors import GrapheneAssetNotFoundError

    check.inst_param(asset_key, "asset_key", AssetKey)
    node = next((n for n in get_asset_nodes(graphene_info) if n.assetKey == asset_key), None)
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

    tags = instance.get_asset_tags(asset_key)
    return GrapheneAsset(key=asset_key, definition=asset_node, tags=tags)


def get_asset_events(graphene_info, asset_key, partitions=None, limit=None, before_timestamp=None):
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

    records = graphene_info.context.instance.all_logs(run_id)
    asset_keys = [
        record.dagster_event.asset_key
        for record in records
        if record.is_dagster_event and record.dagster_event.asset_key
    ]
    return [GrapheneAsset(key=asset_key) for asset_key in asset_keys]
