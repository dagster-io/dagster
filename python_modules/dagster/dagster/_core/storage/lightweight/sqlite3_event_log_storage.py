"""Stdlib-``sqlite3`` event log storage (lightweight dagster).

A dependency-free reimplementation of the event-log surface needed for local,
in-process execution. Replaces the SQLAlchemy + alembic backed
``InMemoryEventLogStorage`` for the ephemeral instance.

Implements the hot path used by ``materialize()``: storing events, per-run event
records, asset records / latest materializations, and asset event tags.
Concurrency slots, dynamic partitions, asset checks, and freshness state are
stubbed — they are daemon/server features not used by local execution.
"""

import sqlite3
import threading
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime, timezone

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.event_api import EventLogRecord, EventRecordsFilter
from dagster._core.events import DagsterEventType
from dagster._core.events.log import EventLogEntry
from dagster._core.storage.event_log.base import (
    AssetEntry,
    AssetRecord,
    EventLogConnection,
    EventLogCursor,
    EventLogStorage,
)
from dagster._serdes import deserialize_value, serialize_value

_SCHEMA = """
CREATE TABLE IF NOT EXISTS event_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT,
    event TEXT NOT NULL,
    dagster_event_type TEXT,
    timestamp TEXT,
    step_key TEXT,
    asset_key TEXT,
    partition TEXT
);
CREATE TABLE IF NOT EXISTS asset_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_key TEXT UNIQUE,
    last_materialization TEXT,
    last_run_id TEXT,
    asset_details TEXT,
    wipe_timestamp TEXT,
    last_materialization_timestamp TEXT,
    tags TEXT,
    create_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    cached_status_data TEXT
);
CREATE TABLE IF NOT EXISTS asset_event_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    asset_key TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT,
    event_timestamp TEXT
);
CREATE TABLE IF NOT EXISTS dynamic_partitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    partitions_def_name TEXT NOT NULL,
    partition TEXT NOT NULL,
    create_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_events_by_run_id ON event_logs (run_id, id);
CREATE INDEX IF NOT EXISTS idx_events_by_asset ON event_logs (asset_key, dagster_event_type, id);
CREATE INDEX IF NOT EXISTS idx_step_key ON event_logs (step_key);
CREATE INDEX IF NOT EXISTS idx_asset_event_tags ON asset_event_tags (asset_key, key, value);
CREATE UNIQUE INDEX IF NOT EXISTS idx_dynamic_partitions
    ON dynamic_partitions (partitions_def_name, partition);
"""


def _ts_to_naive_str(unix_ts: float) -> str:
    return datetime.fromtimestamp(unix_ts, timezone.utc).replace(tzinfo=None).isoformat(sep=" ")


class Sqlite3EventLogStorage(EventLogStorage):
    """In-memory ``sqlite3`` event log storage for the ephemeral/local instance."""

    def __init__(self, preload=None):
        self._conn = sqlite3.connect(":memory:", check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        self._handlers = defaultdict(set)
        with self._lock:
            self._conn.executescript(_SCHEMA)
            self._conn.commit()
        if preload:
            for payload in preload:
                for log in payload.event_list:
                    self.store_event(log)

    @property
    def is_persistent(self) -> bool:
        return False

    # --- storing events ------------------------------------------------------

    def _event_columns(self, event: EventLogEntry):
        asset_key_str = None
        partition = None
        event_type = None
        if event.is_dagster_event:
            de = event.get_dagster_event()
            event_type = de.event_type_value
            if de.asset_key:
                asset_key_str = de.asset_key.to_string()
                partition = de.partition
        return event_type, asset_key_str, partition

    def store_event(self, event: EventLogEntry) -> None:
        event_type, asset_key_str, partition = self._event_columns(event)
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO event_logs (run_id, event, dagster_event_type, timestamp, "
                "step_key, asset_key, partition) VALUES (?,?,?,?,?,?,?)",
                (
                    event.run_id,
                    serialize_value(event),
                    event_type,
                    _ts_to_naive_str(event.timestamp),
                    event.step_key,
                    asset_key_str,
                    partition,
                ),
            )
            event_id = cur.lastrowid
            if event.is_dagster_event and event.get_dagster_event().asset_key:
                self._store_asset_event(event, event_id)
                self._store_asset_event_tags(event, event_id)
            self._conn.commit()

        # notify watchers
        for handler in list(self._handlers.get(event.run_id, ())):
            try:
                handler(event, EventLogCursor.from_storage_id(event_id).to_string())
            except Exception:
                pass

    def _store_asset_event(self, event: EventLogEntry, event_id: int) -> None:
        de = event.get_dagster_event()
        asset_key_str = de.asset_key.to_string()
        ts = _ts_to_naive_str(event.timestamp)
        values = {"last_materialization_timestamp": ts}
        if de.is_step_materialization:
            values["last_materialization"] = serialize_value(
                EventLogRecord(storage_id=event_id, event_log_entry=event)
            )
            values["last_run_id"] = event.run_id
        elif de.is_asset_materialization_planned:
            values["last_run_id"] = event.run_id

        row = self._conn.execute(
            "SELECT id FROM asset_keys WHERE asset_key = ?", (asset_key_str,)
        ).fetchone()
        if row:
            sets = ", ".join(f"{k} = ?" for k in values)
            self._conn.execute(
                f"UPDATE asset_keys SET {sets} WHERE asset_key = ?",
                (*values.values(), asset_key_str),
            )
        else:
            cols = ", ".join(["asset_key", *values.keys()])
            placeholders = ", ".join("?" * (len(values) + 1))
            self._conn.execute(
                f"INSERT INTO asset_keys ({cols}) VALUES ({placeholders})",
                (asset_key_str, *values.values()),
            )

    def _materialization_or_observation_tags(self, event: EventLogEntry):
        de = event.get_dagster_event()
        try:
            if de.is_step_materialization:
                return de.step_materialization_data.materialization.tags or {}
            if de.is_asset_observation:
                return de.asset_observation_data.asset_observation.tags or {}
        except Exception:
            pass
        return {}

    def _store_asset_event_tags(self, event: EventLogEntry, event_id: int) -> None:
        tags = self._materialization_or_observation_tags(event)
        if not tags:
            return
        de = event.get_dagster_event()
        asset_key_str = de.asset_key.to_string()
        ts = _ts_to_naive_str(event.timestamp)
        for k, v in tags.items():
            self._conn.execute(
                "INSERT INTO asset_event_tags (event_id, asset_key, key, value, event_timestamp) "
                "VALUES (?,?,?,?,?)",
                (event_id, asset_key_str, k, v, ts),
            )

    # --- per-run records -----------------------------------------------------

    def _type_filter(self, of_type):
        if of_type is None:
            return None
        if isinstance(of_type, DagsterEventType):
            return [of_type.value]
        return [t.value for t in of_type]

    def get_records_for_run(
        self, run_id, cursor=None, of_type=None, limit=None, ascending=True
    ) -> EventLogConnection:
        clauses = ["run_id = ?"]
        params: list = [run_id]
        type_vals = self._type_filter(of_type)
        if type_vals:
            clauses.append(f"dagster_event_type IN ({','.join('?' * len(type_vals))})")
            params.extend(type_vals)
        if cursor:
            cur_obj = EventLogCursor.parse(cursor)
            storage_id = cur_obj.storage_id() if cur_obj.is_id_cursor() else cur_obj.offset()
            clauses.append("id > ?" if ascending else "id < ?")
            params.append(storage_id)
        order = "ASC" if ascending else "DESC"
        sql = f"SELECT id, event FROM event_logs WHERE {' AND '.join(clauses)} ORDER BY id {order}"
        if limit:
            sql += f" LIMIT {int(limit)}"
        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
        records = [
            EventLogRecord(
                storage_id=r["id"], event_log_entry=deserialize_value(r["event"], EventLogEntry)
            )
            for r in rows
        ]
        last_id = records[-1].storage_id if records else (cursor and storage_id) or -1
        next_cursor = EventLogCursor.from_storage_id(last_id).to_string()
        has_more = bool(limit and len(records) == limit)
        return EventLogConnection(records=records, cursor=next_cursor, has_more=has_more)

    def get_event_records(
        self, event_records_filter: EventRecordsFilter, limit=None, ascending=False
    ) -> Sequence[EventLogRecord]:
        f = event_records_filter
        clauses, params = [], []
        if f.event_type is not None:
            clauses.append("dagster_event_type = ?")
            params.append(f.event_type.value)
        if f.asset_key:
            clauses.append("asset_key = ?")
            params.append(f.asset_key.to_string())
        if f.asset_partitions:
            clauses.append(f"partition IN ({','.join('?' * len(f.asset_partitions))})")
            params.extend(f.asset_partitions)
        if f.after_cursor is not None:
            clauses.append("id > ?")
            params.append(self._cursor_id(f.after_cursor))
        if f.before_cursor is not None:
            clauses.append("id < ?")
            params.append(self._cursor_id(f.before_cursor))
        if f.after_timestamp is not None:
            clauses.append("timestamp > ?")
            params.append(_ts_to_naive_str(f.after_timestamp))
        if f.before_timestamp is not None:
            clauses.append("timestamp < ?")
            params.append(_ts_to_naive_str(f.before_timestamp))
        if f.storage_ids:
            clauses.append(f"id IN ({','.join('?' * len(f.storage_ids))})")
            params.extend(f.storage_ids)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        order = "ASC" if ascending else "DESC"
        sql = f"SELECT id, event FROM event_logs{where} ORDER BY id {order}"
        if limit:
            sql += f" LIMIT {int(limit)}"
        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
        return [
            EventLogRecord(
                storage_id=r["id"], event_log_entry=deserialize_value(r["event"], EventLogEntry)
            )
            for r in rows
        ]

    def _cursor_id(self, cursor) -> int:
        if isinstance(cursor, int):
            return cursor
        obj = EventLogCursor.parse(str(cursor))
        return obj.storage_id() if obj.is_id_cursor() else obj.offset()

    def delete_events(self, run_id: str) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM event_logs WHERE run_id = ?", (run_id,))
            self._conn.commit()

    # --- assets --------------------------------------------------------------

    def _fetch_asset_rows(self, asset_keys=None):
        with self._lock:
            if asset_keys:
                keys = [k.to_string() for k in asset_keys]
                placeholders = ",".join("?" * len(keys))
                rows = self._conn.execute(
                    f"SELECT * FROM asset_keys WHERE asset_key IN ({placeholders})", keys
                ).fetchall()
            else:
                rows = self._conn.execute("SELECT * FROM asset_keys").fetchall()
        return rows

    def _row_to_asset_record(self, row) -> AssetRecord:
        last_mat = None
        if row["last_materialization"]:
            last_mat = deserialize_value(row["last_materialization"], EventLogRecord)
        return AssetRecord(
            storage_id=row["id"],
            asset_entry=AssetEntry(
                asset_key=AssetKey.from_db_string(row["asset_key"]),
                last_materialization_record=last_mat,
                last_run_id=row["last_run_id"],
                asset_details=None,
                cached_status=None,
            ),
        )

    def get_asset_records(self, asset_keys=None) -> Sequence[AssetRecord]:
        return [self._row_to_asset_record(r) for r in self._fetch_asset_rows(asset_keys)]

    def get_latest_materialization_events(
        self, asset_keys: Iterable[AssetKey]
    ) -> Mapping[AssetKey, EventLogEntry | None]:
        records = {r.asset_entry.asset_key: r for r in self.get_asset_records(list(asset_keys))}
        result: dict[AssetKey, EventLogEntry | None] = {}
        for key in asset_keys:
            record = records.get(key)
            mat = record.asset_entry.last_materialization_record if record else None
            result[key] = mat.event_log_entry if mat else None
        return result

    def has_asset_key(self, asset_key: AssetKey) -> bool:
        with self._lock:
            row = self._conn.execute(
                "SELECT 1 FROM asset_keys WHERE asset_key = ?", (asset_key.to_string(),)
            ).fetchone()
        return bool(row)

    def all_asset_keys(self) -> Sequence[AssetKey]:
        rows = self._fetch_asset_rows()
        keys = [
            AssetKey.from_db_string(r["asset_key"])
            for r in sorted(rows, key=lambda x: x["asset_key"])
        ]
        return [k for k in keys if k]

    def get_event_tags_for_asset(self, asset_key, filter_tags=None, filter_event_id=None):
        clauses = ["asset_key = ?"]
        params = [asset_key.to_string()]
        if filter_event_id is not None:
            clauses.append("event_id = ?")
            params.append(filter_event_id)
        sql = (
            "SELECT event_id, key, value FROM asset_event_tags "
            f"WHERE {' AND '.join(clauses)} ORDER BY event_id"
        )
        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
        by_event: dict[int, dict[str, str]] = defaultdict(dict)
        for r in rows:
            by_event[r["event_id"]][r["key"]] = r["value"]
        result = list(by_event.values())
        if filter_tags:
            result = [
                tags for tags in result if all(tags.get(k) == v for k, v in filter_tags.items())
            ]
        return result

    def wipe(self) -> None:
        with self._lock:
            for table in ("event_logs", "asset_keys", "asset_event_tags", "dynamic_partitions"):
                self._conn.execute(f"DELETE FROM {table}")
            self._conn.commit()

    def wipe_asset(self, asset_key: AssetKey) -> None:
        key = asset_key.to_string()
        with self._lock:
            self._conn.execute("DELETE FROM asset_keys WHERE asset_key = ?", (key,))
            self._conn.execute("DELETE FROM asset_event_tags WHERE asset_key = ?", (key,))
            self._conn.execute("UPDATE event_logs SET asset_key = NULL WHERE asset_key = ?", (key,))
            self._conn.commit()

    def wipe_asset_partitions(self, asset_key, partition_keys) -> None:
        pass

    # --- dynamic partitions --------------------------------------------------

    def get_dynamic_partitions(self, partitions_def_name: str) -> Sequence[str]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT partition FROM dynamic_partitions WHERE partitions_def_name = ? "
                "ORDER BY id",
                (partitions_def_name,),
            ).fetchall()
        return [r["partition"] for r in rows]

    def get_paginated_dynamic_partitions(self, partitions_def_name, limit, ascending, cursor=None):
        from dagster._core.storage.event_log.base import PaginatedResults

        partitions = self.get_dynamic_partitions(partitions_def_name)
        return PaginatedResults(results=partitions, cursor=str(len(partitions)), has_more=False)

    def has_dynamic_partition(self, partitions_def_name: str, partition_key: str) -> bool:
        with self._lock:
            row = self._conn.execute(
                "SELECT 1 FROM dynamic_partitions WHERE partitions_def_name = ? AND partition = ?",
                (partitions_def_name, partition_key),
            ).fetchone()
        return bool(row)

    def add_dynamic_partitions(self, partitions_def_name, partition_keys) -> None:
        with self._lock:
            existing = set(self.get_dynamic_partitions(partitions_def_name))
            for key in partition_keys:
                if key not in existing:
                    self._conn.execute(
                        "INSERT INTO dynamic_partitions (partitions_def_name, partition) "
                        "VALUES (?,?)",
                        (partitions_def_name, key),
                    )
                    existing.add(key)
            self._conn.commit()

    def delete_dynamic_partition(self, partitions_def_name, partition_key) -> None:
        with self._lock:
            self._conn.execute(
                "DELETE FROM dynamic_partitions WHERE partitions_def_name = ? AND partition = ?",
                (partitions_def_name, partition_key),
            )
            self._conn.commit()

    # --- watching ------------------------------------------------------------

    def watch(self, run_id, cursor, callback) -> None:
        self._handlers[run_id].add(callback)

    def end_watch(self, run_id, handler) -> None:
        self._handlers[run_id].discard(handler)

    # --- no-op / maintenance -------------------------------------------------

    def reindex_events(self, print_fn=None, force=False) -> None:
        pass

    def reindex_assets(self, print_fn=None, force=False) -> None:
        pass

    def upgrade(self) -> None:
        pass

    def optimize_for_webserver(self, statement_timeout, pool_recycle, max_overflow) -> None:
        pass

    def update_asset_cached_status_data(self, asset_key, cache_values) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE asset_keys SET cached_status_data = ? WHERE asset_key = ?",
                (serialize_value(cache_values), asset_key.to_string()),
            )
            self._conn.commit()

    def wipe_asset_cached_status(self, asset_key) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE asset_keys SET cached_status_data = NULL WHERE asset_key = ?",
                (asset_key.to_string(),),
            )
            self._conn.commit()

    def can_read_asset_status_cache(self) -> bool:
        return False

    def can_write_asset_status_cache(self) -> bool:
        return False

    def get_materialized_partitions(self, asset_key, before_cursor=None, after_cursor=None):
        clauses = ["asset_key = ?", "dagster_event_type = ?", "partition IS NOT NULL"]
        params = [asset_key.to_string(), DagsterEventType.ASSET_MATERIALIZATION.value]
        if before_cursor is not None:
            clauses.append("id < ?")
            params.append(before_cursor)
        if after_cursor is not None:
            clauses.append("id > ?")
            params.append(after_cursor)
        with self._lock:
            rows = self._conn.execute(
                f"SELECT DISTINCT partition FROM event_logs WHERE {' AND '.join(clauses)}", params
            ).fetchall()
        return {r["partition"] for r in rows}

    # --- unsupported daemon/server features ----------------------------------

    def _empty(self, *a, **k):
        return []

    def get_latest_storage_id_by_partition(self, asset_key, event_type, partitions=None):
        return {}

    def get_latest_tags_by_partition(self, asset_key, event_type, tag_keys, *a, **k):
        return {}

    def get_latest_asset_partition_materialization_attempts_without_materializations(
        self, asset_key, after_storage_id=None
    ):
        return {}

    def get_updated_data_version_partitions(self, asset_key, partitions, since_storage_id):
        return set()

    def fetch_materializations(self, records_filter, limit, cursor=None, ascending=False):
        from dagster._core.event_api import EventRecordsResult

        return EventRecordsResult(records=[], cursor="", has_more=False)

    def fetch_failed_materializations(self, records_filter, limit, cursor=None, ascending=False):
        from dagster._core.event_api import EventRecordsResult

        return EventRecordsResult(records=[], cursor="", has_more=False)

    def fetch_observations(self, records_filter, limit, cursor=None, ascending=False):
        from dagster._core.event_api import EventRecordsResult

        return EventRecordsResult(records=[], cursor="", has_more=False)

    def fetch_run_status_changes(self, records_filter, limit, cursor=None, ascending=False):
        from dagster._core.event_api import EventRecordsResult

        return EventRecordsResult(records=[], cursor="", has_more=False)

    def get_latest_planned_materialization_info(self, asset_key, partition=None):
        return None

    def get_freshness_state_records(self, keys):
        return {}

    # asset checks
    def get_asset_check_execution_history(self, check_key, limit, cursor=None, status=None):
        return []

    def get_latest_asset_check_execution_by_key(self, check_keys):
        return {}

    def get_asset_check_summary_records(self, asset_check_keys):
        return {}

    def get_asset_check_partition_info(self, *a, **k):
        return {}

    # concurrency
    def get_concurrency_keys(self):
        return set()

    def get_concurrency_info(self, concurrency_key):
        from dagster._core.storage.event_log.base import ConcurrencyKeyInfo

        return ConcurrencyKeyInfo(
            concurrency_key=concurrency_key,
            slot_count=0,
            claimed_slots=[],
            pending_steps=[],
            assigned_steps=[],
        )

    def get_concurrency_run_ids(self):
        return set()

    def get_pool_limits(self):
        return []

    def set_concurrency_slots(self, concurrency_key, num) -> None:
        pass

    def initialize_concurrency_limit_to_default(self, concurrency_key) -> bool:
        return False

    def delete_concurrency_limit(self, concurrency_key) -> None:
        pass

    def claim_concurrency_slot(self, concurrency_key, run_id, step_key, priority=None):
        from dagster._core.storage.event_log.base import ConcurrencyClaimStatus

        return ConcurrencyClaimStatus(concurrency_key=concurrency_key, slot_status=None)

    def check_concurrency_claim(self, concurrency_key, run_id, step_key):
        from dagster._core.storage.event_log.base import ConcurrencyClaimStatus

        return ConcurrencyClaimStatus(concurrency_key=concurrency_key, slot_status=None)

    def free_concurrency_slots_for_run(self, run_id) -> None:
        pass

    def free_concurrency_slot_for_step(self, run_id, step_key) -> None:
        pass
