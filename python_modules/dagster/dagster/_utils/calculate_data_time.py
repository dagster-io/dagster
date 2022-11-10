import datetime
import json
from typing import AbstractSet, Dict, Mapping, Optional, Tuple

from dagster import (
    AssetKey,
    DagsterEventType,
    DagsterInstance,
    DagsterInvariantViolationError,
    EventLogRecord,
    EventRecordsFilter,
)
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._utils.cached_method import cached_method
from dagster._utils.merger import merge_dicts


class DataTimeInstanceQueryer:
    """Allows caching queries to the instance while evaluating"""

    def __init__(self, instance: DagsterInstance, asset_graph: AssetGraph):
        self._instance = instance
        self._asset_graph = asset_graph

    @property
    def instance(self) -> DagsterInstance:
        return self._instance

    @property
    def asset_graph(self) -> AssetGraph:
        return self._asset_graph

    def _kvs_key_for_record_id(self, record_id: int) -> str:
        return f".dagster/used_data/{record_id}"

    def set_known_used_data(
        self,
        record_id: int,
        new_known_data: Dict[AssetKey, Tuple[Optional[int], Optional[float]]],
    ):
        if self.instance.run_storage.supports_kvs():
            current_known_data = self.get_known_used_data(record_id)
            known_data = merge_dicts(current_known_data, new_known_data)
            serialized_times = json.dumps(
                {key.to_user_string(): value for key, value in known_data.items()}
            )
            self.instance.run_storage.kvs_set(
                {self._kvs_key_for_record_id(record_id): serialized_times}
            )

    def get_known_used_data(
        self, record_id: int
    ) -> Dict[AssetKey, Tuple[Optional[int], Optional[float]]]:
        """Returns the known upstream ids and timestamps stored on the instance"""
        if self.instance.run_storage.supports_kvs():
            # otherwise, attempt to fetch from the instance key-value store
            kvs_key = self._kvs_key_for_record_id(record_id)
            serialized_times = self.instance.run_storage.kvs_get({kvs_key}).get(kvs_key, "{}")
            return {
                AssetKey.from_user_string(key): tuple(value)  # type:ignore
                for key, value in json.loads(serialized_times).items()
            }
        return {}

    @cached_method
    def get_most_recent_materialization_record(
        self, asset_key: AssetKey, before_cursor: Optional[int] = None
    ) -> Optional[EventLogRecord]:
        records = list(
            self.instance.get_event_records(
                EventRecordsFilter(
                    event_type=DagsterEventType.ASSET_MATERIALIZATION,
                    asset_key=asset_key,
                    before_cursor=before_cursor,
                ),
                ascending=False,
                limit=1,
            )
        )
        return records[0] if records else None

    @cached_method
    def calculate_used_data(
        self,
        asset_key: AssetKey,
        record_id: Optional[int],
        record_timestamp: Optional[float],
        required_keys: AbstractSet[AssetKey],
    ) -> Dict[AssetKey, Tuple[Optional[int], Optional[float]]]:

        if record_id is None:
            return {key: (None, None) for key in required_keys}

        # grab the existing upstream data times already calculated for this record (if any)
        known_data = self.get_known_used_data(record_id)
        if asset_key in required_keys:
            known_data[asset_key] = (record_id, record_timestamp)

        # not all required keys have known values
        unknown_required_keys = required_keys - set(known_data.keys())
        if unknown_required_keys:

            # find the upstream times of each of the parents of this asset
            for parent_key in self.asset_graph.get_parents(asset_key):
                # the set of required keys which are upstream of this parent
                upstream_required_keys = set()
                if parent_key in unknown_required_keys:
                    upstream_required_keys.add(parent_key)
                for upstream_key in self.asset_graph.upstream_key_iterator(parent_key):
                    if upstream_key in unknown_required_keys:
                        upstream_required_keys.add(upstream_key)

                # get the most recent asset materialization for this parent which happened before
                # the current record
                latest_parent_record = self.get_most_recent_materialization_record(
                    asset_key=parent_key, before_cursor=record_id
                )

                # recurse to find the data times of this parent
                for key, tup in self.calculate_used_data(
                    asset_key=parent_key,
                    record_id=latest_parent_record.storage_id if latest_parent_record else None,
                    record_timestamp=latest_parent_record.event_log_entry.timestamp
                    if latest_parent_record
                    else None,
                    required_keys=frozenset(upstream_required_keys),
                ).items():
                    # if root data is missing, this overrides other values
                    if tup == (None, None) or known_data.get(key) == (None, None):
                        known_data[key] = (None, None)
                    else:
                        known_data[key] = min(known_data.get(key, tup), tup)

        return {k: v for k, v in known_data.items() if k in required_keys}

    def get_used_data_times_for_record(
        self,
        record: EventLogRecord,
        upstream_keys: Optional[AbstractSet[AssetKey]] = None,
    ) -> Mapping[AssetKey, Optional[datetime.datetime]]:
        """Method to enable calculating the timestamps of materializations of upstream assets
        which were relevant to a given AssetMaterialization. These timestamps can be calculated relative
        to any upstream asset keys.

        The heart of this functionality is a recursive method which takes a given asset materialization
        and finds the most recent materialization of each of its parents which happened *before* that
        given materialization event.
        """
        if record.asset_key is None:
            raise DagsterInvariantViolationError(
                "Can only calculate data times for records with an `asset_key`."
            )
        if upstream_keys is None:
            upstream_keys = self.asset_graph.get_roots(record.asset_key)

        data = self.calculate_used_data(
            asset_key=record.asset_key,
            record_id=record.storage_id,
            record_timestamp=record.event_log_entry.timestamp,
            required_keys=frozenset(upstream_keys),
        )
        self.set_known_used_data(record.storage_id, new_known_data=data)

        return {
            key: datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
            if timestamp is not None
            else None
            for key, (_, timestamp) in data.items()
        }
