from collections import OrderedDict, defaultdict

from dagster import check
from dagster.core.definitions.events import AssetKey
from dagster.core.events.log import EventRecord
from dagster.serdes import ConfigurableClass

from .base import (
    AssetAwareEventLogStorage,
    EventLogSequence,
    EventLogStorage,
    extract_asset_events_cursor,
)


class InMemoryEventLogStorage(EventLogStorage, AssetAwareEventLogStorage, ConfigurableClass):
    """
    In memory only event log storage. Used by ephemeral DagsterInstance or for testing purposes.

    WARNING: Dagit and other core functionality will not work if this is used on a real DagsterInstance
    """

    def __init__(self, inst_data=None, preload=None):
        self._logs = defaultdict(EventLogSequence)
        self._handlers = defaultdict(set)
        self._inst_data = inst_data
        if preload:
            for payload in preload:
                self._logs[payload.pipeline_run.run_id] = EventLogSequence(payload.event_list)

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {}

    @classmethod
    def from_config_value(cls, inst_data, config_value):
        return cls(inst_data)

    def get_logs_for_run(self, run_id, cursor=-1):
        check.str_param(run_id, "run_id")
        check.int_param(cursor, "cursor")
        check.invariant(
            cursor >= -1,
            "Don't know what to do with negative cursor {cursor}".format(cursor=cursor),
        )

        cursor = cursor + 1
        return self._logs[run_id][cursor:]

    def store_event(self, event):
        check.inst_param(event, "event", EventRecord)
        run_id = event.run_id
        self._logs[run_id] = self._logs[run_id].append(event)
        for handler in self._handlers[run_id]:
            handler(event)

    def delete_events(self, run_id):
        del self._logs[run_id]

    def upgrade(self):
        pass

    def reindex(self, print_fn=lambda _: None, force=False):
        pass

    def wipe(self):
        self._logs = defaultdict(EventLogSequence)

    def watch(self, run_id, _start_cursor, callback):
        self._handlers[run_id].add(callback)

    def end_watch(self, run_id, handler):
        if handler in self._handlers[run_id]:
            self._handlers[run_id].remove(handler)

    @property
    def is_persistent(self):
        return False

    def has_asset_key(self, asset_key: AssetKey) -> bool:
        for records in self._logs.values():
            for record in records:
                if (
                    record.is_dagster_event
                    and record.dagster_event.asset_key
                    and record.dagster_event.asset_key == asset_key
                ):
                    return True
        return False

    def get_all_asset_keys(self, prefix_path=None):
        asset_records = []
        for records in self._logs.values():
            asset_records += [
                record
                for record in records
                if record.is_dagster_event
                and record.dagster_event.asset_key
                and (
                    not prefix_path
                    or record.dagster_event.asset_key.to_string().startswith(
                        AssetKey.get_db_prefix(prefix_path)
                    )
                )
            ]

        asset_events = [
            record.dagster_event
            for record in sorted(asset_records, key=lambda x: x.timestamp, reverse=True)
        ]
        asset_keys = OrderedDict()
        for event in asset_events:
            asset_keys["/".join(event.asset_key.path)] = event.asset_key
        return list(asset_keys.values())

    def get_asset_events(
        self,
        asset_key,
        partitions=None,
        before_cursor=None,
        after_cursor=None,
        limit=None,
        ascending=False,
        include_cursor=False,
        cursor=None,
    ):
        asset_events = []
        for records in self._logs.values():
            asset_events += [
                record
                for record in records
                if record.is_dagster_event
                and record.dagster_event.asset_key == asset_key
                and (not partitions or record.dagster_event.partition in partitions)
            ]

        before_cursor, after_cursor = extract_asset_events_cursor(
            cursor, before_cursor, after_cursor, ascending
        )

        events_with_ids = [
            tuple([event_id, event])
            for event_id, event in enumerate(asset_events)
            if (after_cursor is None or event_id > after_cursor)
            and (before_cursor is None or event_id < before_cursor)
        ]

        events_with_ids = sorted(
            events_with_ids, key=lambda x: x[1].timestamp, reverse=not ascending
        )

        if limit:
            events_with_ids = events_with_ids[:limit]

        if include_cursor:
            return events_with_ids

        return [event for id, event in events_with_ids]

    def get_asset_run_ids(self, asset_key):
        asset_run_ids = set()
        for run_id, records in self._logs.items():
            for record in records:
                if record.is_dagster_event and record.dagster_event.asset_key == asset_key:
                    asset_run_ids.add(run_id)
                    break

        return list(asset_run_ids)

    def wipe_asset(self, asset_key):
        check.inst_param(asset_key, "asset_key", AssetKey)

        for run_id in self._logs.keys():
            updated_records = []
            for record in self._logs[run_id]:
                if (
                    not record.is_dagster_event
                    or not record.dagster_event.asset_key
                    or record.dagster_event.asset_key.to_string() != asset_key.to_string()
                ):
                    # not an asset record
                    updated_records.append(record)
                else:
                    dagster_event = record.dagster_event
                    event_specific_data = dagster_event.event_specific_data
                    materialization = event_specific_data.materialization
                    updated_materialization = materialization._replace(asset_key=None)
                    updated_event_specific_data = event_specific_data._replace(
                        materialization=updated_materialization
                    )
                    updated_dagster_event = dagster_event._replace(
                        event_specific_data=updated_event_specific_data
                    )
                    updated_record = record._replace(dagster_event=updated_dagster_event)
                    updated_records.append(updated_record)
            self._logs[run_id] = updated_records
