from datetime import datetime
from typing import AbstractSet, Mapping, Optional, Tuple

from dagster import EventLogRecord

from ..definitions.events import AssetKey
from ..instance import DagsterInstance

UPSTREAM_MATERIALIZATION_TIMES_TAG = ".dagster/upstream_times"


def get_upstream_materialization_times_for_record(
    instance: DagsterInstance,
    upstream_asset_key_mapping: Mapping[str, AbstractSet[str]],
    relevant_upstream_keys: AbstractSet[AssetKey],
    record: EventLogRecord,
) -> Mapping[AssetKey, Optional[datetime]]:
    from dagster._core.events import DagsterEventType
    from dagster._core.storage.event_log.base import EventRecordsFilter

    def _upstream_key_iterator(asset_key_str):
        for key_str in upstream_asset_key_mapping[asset_key_str]:
            yield key_str
            yield from _upstream_key_iterator(key_str)

    def _get_upstream_times_and_ids(record, required_keys):
        cur_tags = instance.get_asset_event_tags(record.storage_id)
        if UPSTREAM_MATERIALIZATION_TIMES_TAG in cur_tags:
            known_times = cur_tags[UPSTREAM_MATERIALIZATION_TIMES_TAG]
            # already have calculated all the required times
            if not (required_keys - set(known_times.keys())):
                return known_times
        else:
            known_times = {}

        cur_key = record.event_log_entry.dagster_event.event_specific_data.materialization.asset_key
        upstream_key_strs = upstream_asset_key_mapping[cur_key.to_user_string()]

        if cur_key in required_keys:
            known_times[cur_key.to_user_string()] = (
                record.storage_id,
                record.event_log_entry.timestamp,
            )
        else:
            for upstream_key_str in upstream_key_strs:
                upstream_key = AssetKey.from_user_string(upstream_key_str)
                upstream_records = instance.get_event_records(
                    EventRecordsFilter(
                        event_type=DagsterEventType.ASSET_MATERIALIZATION,
                        asset_key=upstream_key,
                        before_cursor=record.storage_id,
                    ),
                    ascending=False,
                    limit=1,
                )
                if not upstream_records:
                    # find all the required keys upstream of this one and set their values to None
                    for k in _upstream_key_iterator(upstream_key_str):
                        if AssetKey.from_user_string(k) in required_keys:
                            known_times[k] = (None, None)
                else:
                    # recurse to find the data times of this parent
                    for key, tup in _get_upstream_times_and_ids(
                        upstream_records[0], required_keys
                    ).items():
                        tup = tuple(tup)
                        # if root data is missing, override other values
                        if tup == (None, None) or known_times.get(key) == (None, None):
                            known_times[key] = (None, None)
                        else:
                            known_times[key] = max(known_times.get(key, tup), tup)

        instance.add_asset_event_tags(
            record.storage_id, {UPSTREAM_MATERIALIZATION_TIMES_TAG: known_times}
        )
        return known_times

    return {
        AssetKey.from_user_string(k): datetime.fromtimestamp(timestamp)
        if timestamp is not None
        else None
        for k, (_, timestamp) in _get_upstream_times_and_ids(
            materialization_record, upstream_keys
        ).items()
    }
