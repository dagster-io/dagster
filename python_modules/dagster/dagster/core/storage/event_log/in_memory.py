import logging
import time
import warnings
from collections import OrderedDict, defaultdict
from typing import Dict, Iterable, Mapping, Optional, Sequence

import dagster._check as check
from dagster.core.assets import AssetDetails
from dagster.core.definitions.events import AssetKey
from dagster.core.events import DagsterEventType
from dagster.core.events.log import EventLogEntry
from dagster.core.storage.event_log.base import AssetEntry, AssetRecord
from dagster.serdes import ConfigurableClass
from dagster.utils import utc_datetime_from_timestamp

from .base import (
    EventLogRecord,
    EventLogStorage,
    EventRecordsFilter,
    RunShardedEventsCursor,
    extract_asset_events_cursor,
)


class InMemoryEventLogStorage(EventLogStorage, ConfigurableClass):
    """
    In memory only event log storage. Used by ephemeral DagsterInstance or for testing purposes.

    WARNING: Dagit and other core functionality will not work if this is used on a real DagsterInstance
    """

    def __init__(self, inst_data=None, preload=None):
        self._logs = defaultdict(list)
        self._handlers = defaultdict(set)
        self._inst_data = inst_data
        self._wiped_asset_keys = defaultdict(float)
        if preload:
            for payload in preload:
                self._logs[payload.pipeline_run.run_id] = payload.event_list
        self._assets = defaultdict(dict)

        super().__init__()

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {}

    @classmethod
    def from_config_value(cls, inst_data, config_value):
        return cls(inst_data)

    def get_logs_for_run(
        self,
        run_id,
        cursor=-1,
        of_type=None,
        limit=None,
    ):
        check.str_param(run_id, "run_id")
        check.int_param(cursor, "cursor")
        check.invariant(
            cursor >= -1,
            "Don't know what to do with negative cursor {cursor}".format(cursor=cursor),
        )

        of_types = (
            (
                {of_type.value}
                if isinstance(of_type, DagsterEventType)
                else (
                    {
                        dagster_event_type.value
                        for dagster_event_type in check.set_param(
                            of_type, "of_type", DagsterEventType
                        )
                    }
                )
            )
            if of_type
            else None
        )

        cursor = cursor + 1
        if of_types:
            events = list(
                filter(
                    lambda r: r.is_dagster_event and r.dagster_event.event_type_value in of_types,
                    self._logs[run_id][cursor:],
                )
            )
        else:
            events = self._logs[run_id][cursor:]

        if limit:
            events = events[:limit]

        return events

    def store_event(self, event):
        check.inst_param(event, "event", EventLogEntry)
        run_id = event.run_id
        self._logs[run_id].append(event)

        if (
            event.is_dagster_event
            and (
                event.dagster_event.is_step_materialization
                or event.dagster_event.is_asset_observation
                or event.dagster_event.is_asset_materialization_planned
            )
            and event.dagster_event.asset_key
        ):
            self.store_asset_event(event)

        # snapshot handlers
        handlers = list(self._handlers[run_id])

        for handler in handlers:
            try:
                handler(event)
            except Exception:
                logging.exception("Exception in callback for event watch on run %s.", run_id)

    def store_asset_event(self, event):
        asset_key = event.dagster_event.asset_key
        asset = self._assets[asset_key] if asset_key in self._assets else {"id": len(self._assets)}

        asset["last_materialization_timestamp"] = utc_datetime_from_timestamp(event.timestamp)
        if event.dagster_event.is_step_materialization:
            materialization = event.dagster_event.step_materialization_data.materialization
            asset["last_materialization"] = event
            asset["tags"] = materialization.tags if materialization.tags else None
        if (
            event.dagster_event.is_step_materialization
            or event.dagster_event.is_asset_materialization_planned
        ):
            asset["last_run_id"] = event.run_id

        self._assets[asset_key] = asset

    def delete_events(self, run_id):
        del self._logs[run_id]

    def upgrade(self):
        pass

    def reindex_events(self, print_fn=None, force=False):
        pass

    def reindex_assets(self, print_fn=None, force=False):
        pass

    def wipe(self):
        self._logs = defaultdict(list)

    def watch(self, run_id, _start_cursor, callback):
        self._handlers[run_id].add(callback)

    def end_watch(self, run_id, handler):
        if handler in self._handlers[run_id]:
            self._handlers[run_id].remove(handler)

    @property
    def is_persistent(self):
        return False

    def get_event_records(
        self,
        event_records_filter: Optional[EventRecordsFilter] = None,
        limit: Optional[int] = None,
        ascending: bool = False,
    ) -> Iterable[EventLogRecord]:
        if not event_records_filter:
            warnings.warn(
                "The use of `get_event_records` without an `EventRecordsFilter` is deprecated and "
                "will begin erroring starting in 0.15.0"
            )

        after_id = (
            (
                event_records_filter.after_cursor.id
                if isinstance(event_records_filter.after_cursor, RunShardedEventsCursor)
                else event_records_filter.after_cursor
            )
            if event_records_filter
            else None
        )
        before_id = (
            (
                event_records_filter.before_cursor.id
                if isinstance(event_records_filter.before_cursor, RunShardedEventsCursor)
                else event_records_filter.before_cursor
            )
            if event_records_filter
            else None
        )

        filtered_events = []

        def _apply_filters(record):
            if not event_records_filter:
                return True

            if (
                event_records_filter.event_type
                and record.dagster_event.event_type_value != event_records_filter.event_type.value
            ):
                return False

            if (
                event_records_filter.asset_key
                and record.dagster_event.asset_key != event_records_filter.asset_key
            ):
                return False

            if (
                event_records_filter.asset_key
                and self._wiped_asset_keys[event_records_filter.asset_key] > record.timestamp
            ):
                return False

            if (
                event_records_filter.asset_partitions
                and record.dagster_event.partition not in event_records_filter.asset_partitions
            ):
                return False

            if (
                event_records_filter.after_timestamp
                and record.timestamp >= event_records_filter.after_timestamp
            ):
                return False

            if (
                event_records_filter.before_timestamp
                and record.timestamp >= event_records_filter.before_timestamp
            ):
                return False
            return True

        for records in self._logs.values():
            filtered_events += list(filter(_apply_filters, records))

        event_records = [
            EventLogRecord(storage_id=event_id, event_log_entry=event)
            for event_id, event in enumerate(filtered_events)
            if (after_id is None or event_id > after_id)
            and (before_id is None or event_id < before_id)
        ]

        event_records = sorted(event_records, key=lambda x: x.storage_id, reverse=not ascending)

        if limit:
            event_records = event_records[:limit]

        return event_records

    def get_asset_records(
        self, asset_keys: Optional[Sequence[AssetKey]] = None
    ) -> Iterable[AssetRecord]:
        records = []
        for asset_key, asset in self._assets.items():
            if not asset_keys or asset_key in asset_keys:
                wipe_timestamp = self._wiped_asset_keys.get(asset_key)
                if (
                    not wipe_timestamp
                    or wipe_timestamp < asset.get("last_materialization_timestamp").timestamp()
                ):
                    records.append(
                        AssetRecord(
                            storage_id=asset["id"],
                            asset_entry=AssetEntry(
                                asset_key=asset_key,
                                last_materialization=asset.get("last_materialization"),
                                last_run_id=asset.get("last_run_id"),
                                asset_details=AssetDetails(last_wipe_timestamp=wipe_timestamp)
                                if wipe_timestamp
                                else None,
                            ),
                        )
                    )
        return records

    def has_asset_key(self, asset_key: AssetKey) -> bool:
        for records in self._logs.values():
            for record in records:
                if (
                    record.is_dagster_event
                    and record.dagster_event.asset_key
                    and record.dagster_event.asset_key == asset_key
                    and self._wiped_asset_keys[record.dagster_event.asset_key] < record.timestamp
                ):
                    return True
        return False

    def all_asset_keys(self):
        asset_records = []
        for records in self._logs.values():
            asset_records += [
                record
                for record in records
                if record.is_dagster_event and record.dagster_event.asset_key
            ]

        asset_events = [
            record.dagster_event
            for record in sorted(asset_records, key=lambda x: x.timestamp, reverse=True)
            if self._wiped_asset_keys[record.dagster_event.asset_key] < record.timestamp
        ]
        asset_keys = OrderedDict()
        for event in asset_events:
            asset_keys["/".join(event.asset_key.path)] = event.asset_key
        return list(asset_keys.values())

    def get_latest_materialization_events(
        self, asset_keys: Sequence[AssetKey]
    ) -> Mapping[AssetKey, Optional[EventLogEntry]]:
        check.list_param(asset_keys, "asset_keys", of_type=AssetKey)

        asset_records = []
        for records in self._logs.values():
            asset_records += [
                record
                for record in records
                if record.is_dagster_event
                and record.dagster_event_type == DagsterEventType.ASSET_MATERIALIZATION
                and record.dagster_event.asset_key
                and record.dagster_event.asset_key in asset_keys
            ]

        materializations_by_key = OrderedDict()
        for record in sorted(asset_records, key=lambda x: x.timestamp, reverse=True):
            if (
                self._wiped_asset_keys[record.dagster_event.asset_key] < record.timestamp
                and record.dagster_event.asset_key not in materializations_by_key
            ):
                materializations_by_key[record.dagster_event.asset_key] = record

        return materializations_by_key

    def get_asset_events(
        self,
        asset_key,
        partitions=None,
        before_cursor=None,
        after_cursor=None,
        limit=None,
        ascending=False,
        include_cursor=False,
        before_timestamp=None,
        cursor=None,
    ):
        before_cursor, after_cursor = extract_asset_events_cursor(
            cursor, before_cursor, after_cursor, ascending
        )
        event_records = self.get_event_records(
            EventRecordsFilter(
                event_type=DagsterEventType.ASSET_MATERIALIZATION,
                asset_key=asset_key,
                asset_partitions=partitions,
                before_cursor=before_cursor,
                after_cursor=after_cursor,
                before_timestamp=before_timestamp,
            ),
            limit=limit,
            ascending=ascending,
        )
        if include_cursor:
            return [tuple([record.storage_id, record.event_log_entry]) for record in event_records]
        else:
            return [record.event_log_entry for record in event_records]

    def get_asset_run_ids(self, asset_key):
        asset_run_ids = set()
        for run_id, records in self._logs.items():
            for record in records:
                if (
                    record.is_dagster_event
                    and record.dagster_event.asset_key == asset_key
                    and self._wiped_asset_keys[record.dagster_event.asset_key] < record.timestamp
                ):
                    asset_run_ids.add(run_id)
                    break

        return list(asset_run_ids)

    def wipe_asset(self, asset_key):
        check.inst_param(asset_key, "asset_key", AssetKey)
        self._wiped_asset_keys[asset_key] = time.time()
        if asset_key in self._assets:
            self._assets[asset_key]["last_run_id"] = None

    def get_materialization_count_by_partition(
        self, asset_keys: Sequence[AssetKey]
    ) -> Mapping[AssetKey, Mapping[str, int]]:
        check.list_param(asset_keys, "asset_keys", of_type=AssetKey)

        materialization_count_by_key_partition: Dict[AssetKey, Dict[str, int]] = {}
        for records in self._logs.values():
            for record in records:
                if (
                    record.is_dagster_event
                    and record.dagster_event.asset_key
                    and record.dagster_event.asset_key in asset_keys
                    and record.dagster_event.event_type_value
                    == DagsterEventType.ASSET_MATERIALIZATION.value
                    and record.dagster_event.partition
                    and self._wiped_asset_keys[record.dagster_event.asset_key] < record.timestamp
                ):
                    asset_key = record.dagster_event.asset_key
                    if asset_key not in materialization_count_by_key_partition:
                        materialization_count_by_partition: Dict[str, int] = {}
                        materialization_count_by_key_partition[
                            asset_key
                        ] = materialization_count_by_partition

                    partition = record.dagster_event.partition
                    if partition not in materialization_count_by_key_partition[asset_key]:
                        materialization_count_by_key_partition[asset_key][partition] = 0
                    materialization_count_by_key_partition[asset_key][partition] += 1

        for asset_key in asset_keys:
            if asset_key not in materialization_count_by_key_partition:
                materialization_count_by_key_partition[asset_key] = {}

        return materialization_count_by_key_partition
