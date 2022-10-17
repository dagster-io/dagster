from typing import AbstractSet, Mapping, Tuple

from ..definitions.events import AssetKey
from ..instance import DagsterInstance

ROOT_DATA_TAG = ".dagster/root_data_ids"


def get_latest_root_data_for_key(
    instance: DagsterInstance,
    asset_key: AssetKey,
    upstream_asset_keys: Mapping[str, AbstractSet[str]],
) -> Mapping[str, Tuple[int, float]]:
    from dagster._core.events import DagsterEventType
    from dagster._core.storage.event_log.base import EventRecordsFilter

    def _get_root_keys(asset_key, upstream_asset_keys):
        def _recursive(key_str):
            upstream_key_strs = upstream_asset_keys[key_str]
            if not upstream_key_strs:
                return {key_str}
            return set().union(
                *(_recursive(upstream_key_str) for upstream_key_str in upstream_key_strs)
            )

        return _recursive(asset_key.to_user_string())

    def _get_root_data(record):
        cur_tags = instance.get_asset_event_tags(record.storage_id)
        if ROOT_DATA_TAG in cur_tags:
            return cur_tags[ROOT_DATA_TAG]

        cur_key = record.event_log_entry.dagster_event.event_specific_data.materialization.asset_key
        upstream_keys = upstream_asset_keys[cur_key.to_user_string()]

        if not upstream_keys:
            root_data = {
                cur_key.to_user_string(): (
                    record.storage_id,
                    record.event_log_entry.timestamp,
                )
            }
        else:
            root_data = {}
            for upstream_key in upstream_keys:
                upstream_records = instance.get_event_records(
                    EventRecordsFilter(
                        event_type=DagsterEventType.ASSET_MATERIALIZATION,
                        asset_key=AssetKey.from_user_string(upstream_key),
                        before_cursor=record.storage_id,
                    ),
                    ascending=False,
                    limit=1,
                )
                if not upstream_records:
                    continue

                upstream_root_data = _get_root_data(upstream_records[0])
                for key, tup in upstream_root_data.items():
                    tup = tuple(tup)
                    root_data[key] = max(root_data.get(key, tup), tup)

        instance.add_asset_event_tags(record.storage_id, {ROOT_DATA_TAG: root_data})
        return root_data

    records = instance.get_event_records(
        EventRecordsFilter(
            event_type=DagsterEventType.ASSET_MATERIALIZATION,
            asset_key=asset_key,
        ),
        ascending=False,
        limit=1,
    )

    if len(records) == 0:
        root_data = {}
    else:
        root_data = _get_root_data(records[0])

    return {
        root_key: root_data.get(root_key, (None, None))
        for root_key in _get_root_keys(asset_key, upstream_asset_keys)
    }
