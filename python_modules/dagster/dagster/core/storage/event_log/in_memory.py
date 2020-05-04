from collections import OrderedDict, defaultdict

import gevent.lock

from dagster import check
from dagster.core.events.log import EventRecord

from .base import AssetAwareEventLogStorage, EventLogSequence, EventLogStorage


class InMemoryEventLogStorage(EventLogStorage, AssetAwareEventLogStorage):
    def __init__(self):
        self._logs = defaultdict(EventLogSequence)
        self._lock = defaultdict(gevent.lock.Semaphore)
        self._handlers = defaultdict(set)

    def get_logs_for_run(self, run_id, cursor=-1):
        check.str_param(run_id, 'run_id')
        check.int_param(cursor, 'cursor')
        check.invariant(
            cursor >= -1,
            'Don\'t know what to do with negative cursor {cursor}'.format(cursor=cursor),
        )

        cursor = cursor + 1
        with self._lock[run_id]:
            return self._logs[run_id][cursor:]

    def store_event(self, event):
        check.inst_param(event, 'event', EventRecord)
        run_id = event.run_id
        with self._lock[run_id]:
            self._logs[run_id] = self._logs[run_id].append(event)
            for handler in self._handlers[run_id]:
                handler(event)

    def delete_events(self, run_id):
        with self._lock[run_id]:
            del self._logs[run_id]
        del self._lock[run_id]

    def wipe(self):
        self._logs = defaultdict(EventLogSequence)
        self._lock = defaultdict(gevent.lock.Semaphore)

    def watch(self, run_id, _start_cursor, callback):
        with self._lock[run_id]:
            self._handlers[run_id].add(callback)

    def end_watch(self, run_id, handler):
        with self._lock[run_id]:
            if handler in self._handlers[run_id]:
                self._handlers[run_id].remove(handler)

    @property
    def is_persistent(self):
        return False

    def get_all_asset_keys(self):
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
        ]
        asset_keys = OrderedDict()
        for event in asset_events:
            asset_keys[event.asset_key] = True
        return list(asset_keys.keys())

    def get_asset_events(self, asset_key, cursor=None, limit=None):
        asset_events = []
        for records in self._logs.values():
            asset_events += [
                record
                for record in records
                if record.is_dagster_event and record.dagster_event.asset_key == asset_key
            ]

        asset_events = sorted(asset_events, key=lambda x: x.timestamp, reverse=True)

        if cursor:
            asset_events = asset_events[cursor:]

        if limit:
            asset_events = asset_events[:limit]

        return asset_events

    def get_asset_run_ids(self, asset_key):
        asset_run_ids = set()
        for run_id, records in self._logs.items():
            for record in records:
                if record.is_dagster_event and record.dagster_event.asset_key == asset_key:
                    asset_run_ids.add(run_id)
                    break

        return list(asset_run_ids)
