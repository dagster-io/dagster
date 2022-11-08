import datetime
import json
from typing import AbstractSet, Dict, Iterator, Mapping, Optional, Tuple, cast

from dagster import AssetKey, DagsterEventType, DagsterInstance, EventLogRecord, EventRecordsFilter
from dagster._core.definitions.asset_graph import AssetGraph


def get_used_upstream_materialization_times_for_record(
    record: EventLogRecord,
    instance: DagsterInstance,
    asset_graph: AssetGraph,
    upstream_keys: AbstractSet[AssetKey],
) -> Mapping[AssetKey, Optional[datetime.datetime]]:
    """Method to enable calculating the timestamps of materializations of upstream assets
    which were relevant to a given AssetMaterialization. These timestamps can be calculated relative
    to any upstream asset keys.

    The heart of this functionality is a recursive method which takes a given asset materialization
    and finds the most recent materialization of each of its parents which happened *before* that
    given materialization event.
    """

    def _storage_key(storage_id: int) -> str:
        return f".dagster-used_upstream_times-{storage_id}"

    _local_cache: Dict[int, Dict[AssetKey, Tuple[Optional[int], Optional[float]]]] = {}

    def _get_known_times(
        storage_id: int,
    ) -> Dict[AssetKey, Tuple[Optional[int], Optional[float]]]:
        if storage_id in _local_cache:
            # fetch from local cache if possible
            return _local_cache[storage_id]
        elif instance.run_storage.supports_kvs():
            # otherwise, attempt to fetch from the instance key-value store
            storage_key = _storage_key(storage_id)
            serialized_times = instance.run_storage.kvs_get({storage_key}).get(storage_key, "{}")
            return {
                AssetKey.from_user_string(key): tuple(value)  # type:ignore
                for key, value in json.loads(serialized_times).items()
            }
        return {}

    def _set_known_times(
        storage_id: int, known_times: Dict[AssetKey, Tuple[Optional[int], Optional[float]]]
    ):
        if known_times != _local_cache.get(storage_id):
            _local_cache[storage_id] = known_times
            if instance.run_storage.supports_kvs():
                # store this info in the instance key-value store for future calls
                storage_key = _storage_key(storage_id)
                serialized_times = json.dumps(
                    {key.to_user_string(): value for key, value in known_times.items()}
                )
                instance.run_storage.kvs_set({storage_key: serialized_times})

    def _upstream_key_iterator(key: AssetKey) -> Iterator[AssetKey]:
        yield key
        for parent_key in asset_graph.get_parents(key):
            yield from _upstream_key_iterator(parent_key)

    def _get_upstream_ids_and_times(
        record: Optional[EventLogRecord], required_keys: AbstractSet[AssetKey]
    ) -> Dict[AssetKey, Tuple[Optional[int], Optional[float]]]:

        if record is None:
            return {key: (None, None) for key in required_keys}

        key = cast(AssetKey, record.asset_key)

        # grab the existing upstream data times already calculated for this record (if any)
        known_times = _get_known_times(record.storage_id)
        if key in required_keys:
            known_times[key] = (
                record.storage_id,
                record.event_log_entry.timestamp,
            )

        # not all required keys have known values
        unknown_required_keys = required_keys - set(known_times.keys())
        if unknown_required_keys:

            # find the upstream times of each of the parents of this asset
            for parent_key in asset_graph.get_parents(key):
                # the set of required keys which are upstream of this key
                upstream_required_keys = set()
                for upstream_key in _upstream_key_iterator(parent_key):
                    if upstream_key in unknown_required_keys:
                        upstream_required_keys.add(upstream_key)

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
                for key, tup in _get_upstream_ids_and_times(
                    latest_parent_record, upstream_required_keys
                ).items():
                    # if root data is missing, this overrides other values
                    if tup == (None, None) or known_times.get(key) == (None, None):
                        known_times[key] = (None, None)
                    else:
                        known_times[key] = min(known_times.get(key, tup), tup)

        # cache these calculated values
        _set_known_times(record.storage_id, known_times)

        return {k: v for k, v in known_times.items() if k in required_keys}

    return {
        # convert to nicer output format
        k: datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
        if timestamp is not None
        else None
        for k, (_, timestamp) in _get_upstream_ids_and_times(record, upstream_keys).items()
    }
