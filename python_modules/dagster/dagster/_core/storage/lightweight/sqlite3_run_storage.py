"""Stdlib-``sqlite3`` run storage (lightweight dagster).

A dependency-free reimplementation of the run-storage surface needed for local,
in-process execution (``materialize()`` / ``execute_in_process``). Replaces the
SQLAlchemy + alembic backed ``InMemoryRunStorage`` for the ephemeral instance.

Distributed/daemon-only features (backfills, daemon heartbeats, run groups,
partition data, telemetry cursors) are stubbed with empty/no-op behavior — they
are not exercised by local materialization.
"""

import sqlite3
import threading
import zlib
from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from enum import Enum

from dagster._core.errors import DagsterRunNotFoundError
from dagster._core.events import EVENT_TYPE_TO_PIPELINE_RUN_STATUS
from dagster._core.snap import JobSnap
from dagster._core.snap.execution_plan_snapshot import (
    ExecutionPlanSnapshot,
    create_execution_plan_snapshot_id,
)
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus, RunRecord, RunsFilter
from dagster._core.storage.runs.base import RunStorage
from dagster._core.storage.tags import BACKFILL_ID_TAG, PARTITION_NAME_TAG, PARTITION_SET_TAG
from dagster._serdes import deserialize_value, serialize_value


class SnapshotType(Enum):
    # Local copy of dagster._core.storage.runs.sql_run_storage.SnapshotType, defined
    # here to avoid importing the sqlalchemy-backed sql_run_storage module.
    PIPELINE = "PIPELINE"
    EXECUTION_PLAN = "EXECUTION_PLAN"


_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT UNIQUE,
    snapshot_id TEXT,
    pipeline_name TEXT,
    status TEXT,
    run_body TEXT,
    partition TEXT,
    partition_set TEXT,
    create_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    start_time REAL,
    end_time REAL,
    backfill_id TEXT
);
CREATE TABLE IF NOT EXISTS run_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT,
    key TEXT,
    value TEXT
);
CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id TEXT UNIQUE NOT NULL,
    snapshot_body BLOB NOT NULL,
    snapshot_type TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS kvs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL,
    value TEXT
);
CREATE INDEX IF NOT EXISTS idx_run_tags ON run_tags (key, value);
CREATE INDEX IF NOT EXISTS idx_run_tags_run_idx ON run_tags (run_id, id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_kvs_keys_unique ON kvs (key);
"""


def _now_naive_utc_str() -> str:
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat(sep=" ")


def _parse_naive_utc(value) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        dt = value
    else:
        dt = datetime.fromisoformat(str(value))
    return dt.replace(tzinfo=timezone.utc)


class Sqlite3RunStorage(RunStorage):
    """In-memory ``sqlite3`` run storage for the ephemeral/local instance."""

    def __init__(self, preload=None):
        # A single shared in-memory connection for the life of the instance.
        self._conn = sqlite3.connect(":memory:", check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        with self._lock:
            self._conn.executescript(_SCHEMA)
            self._conn.commit()
        if preload:
            for payload in preload:
                for run in payload.dagster_run_list:
                    self.add_run(run)

    # --- runs ----------------------------------------------------------------

    def _get_run_by_id(self, run_id: str) -> DagsterRun | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT run_body, status FROM runs WHERE run_id = ?", (run_id,)
            ).fetchone()
        if not row:
            return None
        return self._row_to_run(row)

    def _row_to_run(self, row) -> DagsterRun:
        run = deserialize_value(row["run_body"], DagsterRun)
        return run.with_status(DagsterRunStatus(row["status"]))

    def add_run(self, dagster_run: DagsterRun) -> DagsterRun:
        tags = dagster_run.tags
        with self._lock:
            self._conn.execute(
                "INSERT INTO runs (run_id, pipeline_name, status, run_body, snapshot_id, "
                "partition, partition_set, backfill_id, create_timestamp, update_timestamp) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    dagster_run.run_id,
                    dagster_run.job_name,
                    dagster_run.status.value,
                    serialize_value(dagster_run),
                    dagster_run.job_snapshot_id,
                    tags.get(PARTITION_NAME_TAG),
                    tags.get(PARTITION_SET_TAG),
                    tags.get(BACKFILL_ID_TAG),
                    _now_naive_utc_str(),
                    _now_naive_utc_str(),
                ),
            )
            for k, v in dagster_run.tags_for_storage().items():
                self._conn.execute(
                    "INSERT INTO run_tags (run_id, key, value) VALUES (?,?,?)",
                    (dagster_run.run_id, k, v),
                )
            self._conn.commit()
        return dagster_run

    def add_historical_run(self, dagster_run, run_creation_time) -> DagsterRun:
        return self.add_run(dagster_run)

    def handle_run_event(self, run_id, event, update_timestamp=None) -> None:
        if event.event_type not in EVENT_TYPE_TO_PIPELINE_RUN_STATUS:
            return
        run = self._get_run_by_id(run_id)
        if run is None:
            return
        new_status = EVENT_TYPE_TO_PIPELINE_RUN_STATUS[event.event_type]
        updated_run = run.with_status(new_status)
        ts = update_timestamp or datetime.now(timezone.utc)

        sets = ["run_body = ?", "status = ?", "update_timestamp = ?"]
        params = [
            serialize_value(updated_run),
            new_status.value,
            ts.replace(tzinfo=None).isoformat(sep=" "),
        ]
        if new_status == DagsterRunStatus.STARTED:
            sets.append("start_time = ?")
            params.append(ts.timestamp())
        elif new_status in (
            DagsterRunStatus.CANCELED,
            DagsterRunStatus.FAILURE,
            DagsterRunStatus.SUCCESS,
        ):
            sets.append("end_time = ?")
            params.append(ts.timestamp())
        params.append(run_id)
        with self._lock:
            self._conn.execute(f"UPDATE runs SET {', '.join(sets)} WHERE run_id = ?", params)
            self._conn.commit()

    # --- query helpers -------------------------------------------------------

    def _filter_clause(self, filters: RunsFilter | None):
        if not filters:
            return "", []
        clauses, params = [], []
        if filters.run_ids:
            clauses.append(f"run_id IN ({','.join('?' * len(filters.run_ids))})")
            params.extend(filters.run_ids)
        if filters.job_name:
            clauses.append("pipeline_name = ?")
            params.append(filters.job_name)
        if filters.statuses:
            clauses.append(f"status IN ({','.join('?' * len(filters.statuses))})")
            params.extend(s.value for s in filters.statuses)
        if filters.snapshot_id:
            clauses.append("snapshot_id = ?")
            params.append(filters.snapshot_id)
        if filters.tags:
            # tag filters require a join against run_tags for each tag
            for key, value in filters.tags.items():
                values = value if isinstance(value, (list, tuple, set)) else [value]
                placeholders = ",".join("?" * len(values))
                clauses.append(
                    "run_id IN (SELECT run_id FROM run_tags WHERE key = ? "
                    f"AND value IN ({placeholders}))"
                )
                params.append(key)
                params.extend(values)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        return where, params

    def get_runs(self, filters=None, cursor=None, limit=None, bucket_by=None, ascending=False):
        where, params = self._filter_clause(filters)
        order = "ASC" if ascending else "DESC"
        sql = f"SELECT run_body, status FROM runs{where} ORDER BY id {order}"
        if limit:
            sql += f" LIMIT {int(limit)}"
        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
        return [self._row_to_run(r) for r in rows]

    def get_runs_count(self, filters=None) -> int:
        where, params = self._filter_clause(filters)
        with self._lock:
            row = self._conn.execute(f"SELECT COUNT(*) AS c FROM runs{where}", params).fetchone()
        return row["c"]

    def get_run_records(
        self, filters=None, limit=None, order_by=None, ascending=False, cursor=None, bucket_by=None
    ) -> Sequence[RunRecord]:
        where, params = self._filter_clause(filters)
        order = "ASC" if ascending else "DESC"
        sql = (
            "SELECT id, run_body, status, create_timestamp, update_timestamp, "
            f"start_time, end_time FROM runs{where} ORDER BY id {order}"
        )
        if limit:
            sql += f" LIMIT {int(limit)}"
        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
        return [
            RunRecord(
                storage_id=r["id"],
                dagster_run=self._row_to_run(r),
                create_timestamp=_parse_naive_utc(r["create_timestamp"]),
                update_timestamp=_parse_naive_utc(r["update_timestamp"]),
                start_time=r["start_time"],
                end_time=r["end_time"],
            )
            for r in rows
        ]

    def get_run_ids(self, filters=None, cursor=None, limit=None) -> Sequence[str]:
        where, params = self._filter_clause(filters)
        sql = f"SELECT run_id FROM runs{where} ORDER BY id ASC"
        if limit:
            sql += f" LIMIT {int(limit)}"
        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
        return [r["run_id"] for r in rows]

    def has_run(self, run_id: str) -> bool:
        return self._get_run_by_id(run_id) is not None

    def delete_run(self, run_id: str) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM runs WHERE run_id = ?", (run_id,))
            self._conn.execute("DELETE FROM run_tags WHERE run_id = ?", (run_id,))
            self._conn.commit()

    def get_run_group(self, run_id: str):
        run = self._get_run_by_id(run_id)
        if run is None:
            raise DagsterRunNotFoundError(invalid_run_id=run_id)
        root = run.root_run_id or run.run_id
        return (root, [run])

    def replace_job_origin(self, run, job_origin) -> None:
        updated = run._replace(
            remote_job_origin=job_origin, job_code_origin=job_origin.repository_origin.code_pointer
        )  # type: ignore
        with self._lock:
            self._conn.execute(
                "UPDATE runs SET run_body = ? WHERE run_id = ?",
                (serialize_value(updated), run.run_id),
            )
            self._conn.commit()

    # --- tags ----------------------------------------------------------------

    def add_run_tags(self, run_id: str, new_tags: Mapping[str, str]) -> None:
        run = self._get_run_by_id(run_id)
        if run is None:
            raise DagsterRunNotFoundError(invalid_run_id=run_id)
        current = dict(run.tags)
        with self._lock:
            existing = {
                r["key"]
                for r in self._conn.execute(
                    "SELECT key FROM run_tags WHERE run_id = ?", (run_id,)
                ).fetchall()
            }
            for k, v in new_tags.items():
                if k in existing:
                    self._conn.execute(
                        "UPDATE run_tags SET value = ? WHERE run_id = ? AND key = ?", (v, run_id, k)
                    )
                else:
                    self._conn.execute(
                        "INSERT INTO run_tags (run_id, key, value) VALUES (?,?,?)", (run_id, k, v)
                    )
            merged = {**current, **new_tags}
            updated_run = run.with_tags(merged)
            self._conn.execute(
                "UPDATE runs SET run_body = ?, partition = ?, partition_set = ? WHERE run_id = ?",
                (
                    serialize_value(updated_run),
                    merged.get(PARTITION_NAME_TAG),
                    merged.get(PARTITION_SET_TAG),
                    run_id,
                ),
            )
            self._conn.commit()

    def get_run_tags(self, tag_keys, value_prefix=None, limit=None):
        result = defaultdict(set)
        placeholders = ",".join("?" * len(tag_keys))
        sql = f"SELECT DISTINCT key, value FROM run_tags WHERE key IN ({placeholders})"
        params = list(tag_keys)
        if value_prefix:
            sql += " AND value LIKE ?"
            params.append(value_prefix + "%")
        if limit:
            sql += f" LIMIT {int(limit)}"
        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
        for r in rows:
            result[r["key"]].add(r["value"])
        return sorted(((k, v) for k, v in result.items()), key=lambda x: x[0])

    def get_run_tag_keys(self):
        with self._lock:
            rows = self._conn.execute("SELECT DISTINCT key FROM run_tags ORDER BY key").fetchall()
        return sorted(r["key"] for r in rows)

    # --- snapshots -----------------------------------------------------------

    def _add_snapshot(self, snapshot_id: str, snapshot_obj, snapshot_type: SnapshotType) -> str:
        with self._lock:
            try:
                self._conn.execute(
                    "INSERT INTO snapshots (snapshot_id, snapshot_body, snapshot_type) "
                    "VALUES (?,?,?)",
                    (
                        snapshot_id,
                        zlib.compress(serialize_value(snapshot_obj).encode("utf-8")),
                        snapshot_type.value,
                    ),
                )
                self._conn.commit()
            except sqlite3.IntegrityError:
                pass
        return snapshot_id

    def _get_snapshot(self, snapshot_id: str):
        with self._lock:
            row = self._conn.execute(
                "SELECT snapshot_body FROM snapshots WHERE snapshot_id = ?", (snapshot_id,)
            ).fetchone()
        if not row:
            return None
        decoded = zlib.decompress(row["snapshot_body"]).decode("utf-8")
        return deserialize_value(decoded, (ExecutionPlanSnapshot, JobSnap))

    def _has_snapshot_id(self, snapshot_id: str) -> bool:
        with self._lock:
            row = self._conn.execute(
                "SELECT 1 FROM snapshots WHERE snapshot_id = ?", (snapshot_id,)
            ).fetchone()
        return bool(row)

    def add_job_snapshot(self, job_snapshot: JobSnap) -> str:
        return self._add_snapshot(job_snapshot.snapshot_id, job_snapshot, SnapshotType.PIPELINE)

    def get_job_snapshot(self, job_snapshot_id: str) -> JobSnap:
        return self._get_snapshot(job_snapshot_id)

    def has_job_snapshot(self, job_snapshot_id: str) -> bool:
        return self._has_snapshot_id(job_snapshot_id)

    def add_execution_plan_snapshot(self, execution_plan_snapshot: ExecutionPlanSnapshot) -> str:
        snapshot_id = create_execution_plan_snapshot_id(execution_plan_snapshot)
        return self._add_snapshot(snapshot_id, execution_plan_snapshot, SnapshotType.EXECUTION_PLAN)

    def get_execution_plan_snapshot(self, execution_plan_snapshot_id: str) -> ExecutionPlanSnapshot:
        return self._get_snapshot(execution_plan_snapshot_id)

    def has_execution_plan_snapshot(self, execution_plan_snapshot_id: str) -> bool:
        return self._has_snapshot_id(execution_plan_snapshot_id)

    # --- key-value store (cursors) ------------------------------------------

    def set_cursor_values(self, pairs: Mapping[str, str]) -> None:
        with self._lock:
            for k, v in pairs.items():
                self._conn.execute(
                    "INSERT INTO kvs (key, value) VALUES (?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                    (k, v),
                )
            self._conn.commit()

    def get_cursor_values(self, keys):
        placeholders = ",".join("?" * len(keys))
        with self._lock:
            rows = self._conn.execute(
                f"SELECT key, value FROM kvs WHERE key IN ({placeholders})", list(keys)
            ).fetchall()
        return {r["key"]: r["value"] for r in rows}

    # --- maintenance ---------------------------------------------------------

    def wipe(self) -> None:
        with self._lock:
            for table in ("runs", "run_tags", "snapshots", "kvs"):
                self._conn.execute(f"DELETE FROM {table}")
            self._conn.commit()

    def get_run_partition_data(self, runs_filter) -> Sequence:
        return []

    def upgrade(self) -> None:
        pass

    def optimize_for_webserver(self, statement_timeout, pool_recycle, max_overflow) -> None:
        pass

    @property
    def supports_bucket_queries(self) -> bool:
        return False

    def dispose(self) -> None:
        with self._lock:
            self._conn.close()

    # --- daemon / backfill (not supported in lightweight local mode) ---------

    def _unsupported(self, feature: str):
        raise NotImplementedError(
            f"{feature} is not supported by the lightweight sqlite3 run storage "
            "(local in-process execution only)."
        )

    def add_daemon_heartbeat(self, daemon_heartbeat) -> None:
        pass

    def get_daemon_heartbeats(self):
        return {}

    def wipe_daemon_heartbeats(self) -> None:
        pass

    def add_backfill(self, partition_backfill) -> None:
        self._unsupported("Backfills")

    def update_backfill(self, partition_backfill) -> None:
        self._unsupported("Backfills")

    def get_backfill(self, backfill_id):
        return None

    def get_backfills(self, filters=None, cursor=None, limit=None, status=None):
        return []

    def get_backfills_count(self, filters=None) -> int:
        return 0
