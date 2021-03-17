from dagster import check
from dagster.core.definitions.events import AssetKey
from dagster.core.events import DagsterEventType

from .utils import capture_error


@capture_error
def get_assets(graphene_info):
    from ..schema.pipelines.pipeline import GrapheneAsset
    from ..schema.roots.assets import GrapheneAssetConnection

    instance = graphene_info.context.instance

    asset_keys = instance.all_asset_keys()
    asset_tags_by_key = instance.all_asset_tags()
    return GrapheneAssetConnection(
        nodes=[
            GrapheneAsset(key=asset_key, tags=asset_tags_by_key.get(asset_key, {}))
            for asset_key in asset_keys
        ]
    )


def get_asset(graphene_info, asset_key):
    from ..schema.errors import GrapheneAssetNotFoundError
    from ..schema.pipelines.pipeline import GrapheneAsset

    check.inst_param(asset_key, "asset_key", AssetKey)
    instance = graphene_info.context.instance

    if not instance.has_asset_key(asset_key):
        return GrapheneAssetNotFoundError(asset_key=asset_key)

    tags = instance.get_asset_tags(asset_key)
    return GrapheneAsset(key=asset_key, tags=tags)


def get_asset_events(graphene_info, asset_key, partitions=None, cursor=None, limit=None):
    check.inst_param(asset_key, "asset_key", AssetKey)
    check.opt_str_param(cursor, "cursor")
    check.opt_int_param(limit, "limit")
    instance = graphene_info.context.instance
    events = instance.events_for_asset_key(
        asset_key, partitions=partitions, before_cursor=cursor, limit=limit
    )
    return [
        event
        for record_id, event in events
        if event.is_dagster_event
        and event.dagster_event.event_type_value == DagsterEventType.ASSET_MATERIALIZATION.value
    ]


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
