from datetime import datetime
from typing import AbstractSet, Mapping, Optional, cast

from dagster import AssetKey, DagsterEventType, DagsterInstance, EventLogRecord, EventRecordsFilter

UPSTREAM_MATERIALIZATION_TIMES_TAG = ".dagster/upstream_times"


def get_upstream_materialization_times_for_record(
    instance: DagsterInstance,
    upstream_asset_key_mapping: Mapping[str, AbstractSet[str]],
    relevant_upstream_keys: AbstractSet[AssetKey],
    record: EventLogRecord,
) -> Mapping[AssetKey, Optional[datetime]]:
    """Helper method to enable calculating the timestamps of materializations of upstream assets
    which were relevant to a given AssetMaterialization. These timestamps can be calculated relative
    to any upstream asset keys.

    The heart of this functionality is a recursive method which takes a given asset materialization
    and finds the most recent materialization of each of its parents which happened *before* that
    given materialization event.
    """

    def _upstream_key_str_iterator(asset_key_str: str):
        for key_str in upstream_asset_key_mapping[asset_key_str]:
            yield key_str
            yield from _upstream_key_str_iterator(key_str)

    def _get_upstream_times_and_ids(record: EventLogRecord, required_keys: AbstractSet[AssetKey]):
        # no record available, so the data time for all keys upstream of here is None
        if record is None:
            return {k: (None, None) for k in required_keys}

        cur_tags = instance.get_asset_event_tags(record.storage_id)

        cur_key = cast(AssetKey, record.asset_key)
        cur_key_str = cur_key.to_user_string()

        # grab the existing upstream data times already calculated for this record (if any)
        if UPSTREAM_MATERIALIZATION_TIMES_TAG in cur_tags:
            known_times = cur_tags[UPSTREAM_MATERIALIZATION_TIMES_TAG]
        else:
            known_times = {}

        # this is a required key to track, so grab its record
        if cur_key in required_keys:
            known_times[cur_key_str] = (
                record.storage_id,
                record.event_log_entry.timestamp,
            )

        # not all required data times are present in the tags
        if required_keys - set(known_times.keys()):

            # find all the required keys that are upstream of this key
            required_upstream_keys = set()
            for upstream_key_str in _upstream_key_str_iterator(cur_key_str):
                upstream_key = AssetKey.from_user_string(upstream_key_str)
                if upstream_key in required_keys:
                    required_upstream_keys.add(upstream_key)

            # find the upstream times of each of the parents of this asset
            for parent_key_str in upstream_asset_key_mapping[cur_key_str]:
                parent_key = AssetKey.from_user_string(parent_key_str)

                # get the most recent asset materialization for this parent which happened before
                # the current record
                parent_records = instance.get_event_records(
                    EventRecordsFilter(
                        event_type=DagsterEventType.ASSET_MATERIALIZATION,
                        asset_key=parent_key,
                        before_cursor=record.storage_id,
                    ),
                    ascending=False,
                    limit=1,
                )
                latest_parent_record = parent_records[0] if parent_records else None

                # recurse to find the data times of this parent
                for key, tup in _get_upstream_times_and_ids(
                    latest_parent_record, required_upstream_keys
                ).items():
                    tup = tuple(tup)
                    # if root data is missing, override other values
                    if tup == (None, None) or known_times.get(key) == (None, None):
                        known_times[key] = (None, None)
                    else:
                        known_times[key] = min(tuple(known_times.get(key, tup)), tup)

        # cache asset event in the database
        instance.add_asset_event_tags(
            record.storage_id, {UPSTREAM_MATERIALIZATION_TIMES_TAG: known_times}
        )
        return {
            k: v
            for k, v in known_times.items()
            # filter out unnecessary info
            if AssetKey.from_user_string(k) in required_keys
        }

    return {
        # convert to nicer output format
        AssetKey.from_user_string(k): datetime.fromtimestamp(timestamp)
        if timestamp is not None
        else None
        for k, (_, timestamp) in _get_upstream_times_and_ids(record, relevant_upstream_keys).items()
    }
