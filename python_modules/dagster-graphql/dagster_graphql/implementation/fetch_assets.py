from dagster import AssetKey, DagsterEventType, EventRecordsFilter, check

from .utils import capture_error


@capture_error
def get_assets(graphene_info):
    from ..schema.pipelines.pipeline import GrapheneAsset
    from ..schema.roots.assets import GrapheneAssetConnection

    instance = graphene_info.context.instance

    asset_keys = instance.all_asset_keys()
    return GrapheneAssetConnection(nodes=[GrapheneAsset(key=asset_key) for asset_key in asset_keys])


def get_asset(graphene_info, asset_key):
    from ..schema.errors import GrapheneAssetNotFoundError
    from ..schema.pipelines.pipeline import GrapheneAsset

    check.inst_param(asset_key, "asset_key", AssetKey)
    instance = graphene_info.context.instance

    if not instance.has_asset_key(asset_key):
        return GrapheneAssetNotFoundError(asset_key=asset_key)

    tags = instance.get_asset_tags(asset_key)
    return GrapheneAsset(key=asset_key, tags=tags)


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
