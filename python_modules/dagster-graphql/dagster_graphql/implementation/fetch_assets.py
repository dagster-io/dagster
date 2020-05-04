from dagster import check
from dagster.core.events import DagsterEventType
from dagster.core.storage.event_log.base import AssetAwareEventLogStorage


def get_assets(graphene_info):
    event_storage = (
        graphene_info.context.instance._event_storage  # pylint: disable=protected-access
    )
    if not isinstance(event_storage, AssetAwareEventLogStorage):
        return graphene_info.schema.type_named('AssetsNotSupportedError')(
            message='The configured event log storage is not asset aware.'
        )

    asset_keys = event_storage.get_all_asset_keys()
    return graphene_info.schema.type_named('AssetConnection')(
        nodes=[graphene_info.schema.type_named('Asset')(key=asset_key) for asset_key in asset_keys]
    )


def get_asset(graphene_info, asset_key):
    event_storage = (
        graphene_info.context.instance._event_storage  # pylint: disable=protected-access
    )

    if not isinstance(event_storage, AssetAwareEventLogStorage):
        return graphene_info.schema.type_named('AssetsNotSupportedError')(
            message='The configured event log storage is not asset aware.'
        )

    return graphene_info.schema.type_named('Asset')(key=asset_key)


def get_asset_events(graphene_info, asset_key, cursor=None, limit=None):
    check.str_param(asset_key, 'asset_key')
    check.opt_str_param(cursor, 'cursor')
    check.opt_int_param(limit, 'limit')
    event_storage = (
        graphene_info.context.instance._event_storage  # pylint: disable=protected-access
    )
    check.inst(event_storage, AssetAwareEventLogStorage)
    events = event_storage.get_asset_events(asset_key, cursor, limit)
    return [
        event
        for event in events
        if event.is_dagster_event
        and event.dagster_event.event_type_value == DagsterEventType.STEP_MATERIALIZATION.value
    ]


def get_asset_run_ids(graphene_info, asset_key):
    check.str_param(asset_key, 'asset_key')
    event_storage = (
        graphene_info.context.instance._event_storage  # pylint: disable=protected-access
    )
    check.inst(event_storage, AssetAwareEventLogStorage)
    run_ids = event_storage.get_asset_run_ids(asset_key)
    return run_ids
