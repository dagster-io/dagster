import glob
import logging
import os
import sqlite3
import threading
import time
import warnings
from collections import defaultdict
from contextlib import contextmanager
from typing import Iterable, Optional

import sqlalchemy as db
from sqlalchemy.pool import NullPool
from tqdm import tqdm
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

import dagster._check as check
import dagster.seven as seven
from dagster.config.source import StringSource
from dagster.core.events import DagsterEventType
from dagster.core.events.log import EventLogEntry
from dagster.core.storage.event_log.base import EventLogRecord, EventRecordsFilter
from dagster.core.storage.pipeline_run import PipelineRunStatus, RunsFilter
from dagster.core.storage.sql import (
    check_alembic_revision,
    create_engine,
    get_alembic_config,
    run_alembic_upgrade,
    stamp_alembic_rev,
)
from dagster.core.storage.sqlite import create_db_conn_string
from dagster.serdes import (
    ConfigurableClass,
    ConfigurableClassData,
    deserialize_json_to_dagster_namedtuple,
)
from dagster.utils import mkdir_p

from ..schema import SqlEventLogStorageMetadata, SqlEventLogStorageTable
from ..sql_event_log import RunShardedEventsCursor, SqlEventLogStorage

INDEX_SHARD_NAME = "index"


class SqliteEventLogStorage(SqlEventLogStorage, ConfigurableClass):
    """SQLite-backed event log storage.

    Users should not directly instantiate this class; it is instantiated by internal machinery when
    ``dagit`` and ``dagster-graphql`` load, based on the values in the ``dagster.yaml`` file in
    ``$DAGSTER_HOME``. Configuration of this class should be done by setting values in that file.

    This is the default event log storage when none is specified in the ``dagster.yaml``.

    To explicitly specify SQLite for event log storage, you can add a block such as the following
    to your ``dagster.yaml``:

    .. code-block:: YAML

        event_log_storage:
          module: dagster.core.storage.event_log
          class: SqliteEventLogStorage
          config:
            base_dir: /path/to/dir

    The ``base_dir`` param tells the event log storage where on disk to store the databases. To
    improve concurrent performance, event logs are stored in a separate SQLite database for each
    run.
    """

    def __init__(self, base_dir, inst_data=None):
        """Note that idempotent initialization of the SQLite database is done on a per-run_id
        basis in the body of connect, since each run is stored in a separate database."""
        self._base_dir = os.path.abspath(check.str_param(base_dir, "base_dir"))
        mkdir_p(self._base_dir)

        self._obs = None

        self._watchers = defaultdict(dict)
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)

        # Used to ensure that each run ID attempts to initialize its DB the first time it connects,
        # ensuring that the database will be created if it doesn't exist
        self._initialized_dbs = set()

        # Ensure that multiple threads (like the event log watcher) interact safely with each other
        self._db_lock = threading.Lock()

        if not os.path.exists(self.path_for_shard(INDEX_SHARD_NAME)):
            conn_string = self.conn_string_for_shard(INDEX_SHARD_NAME)
            engine = create_engine(conn_string, poolclass=NullPool)
            self._initdb(engine)
            self.reindex_events()
            self.reindex_assets()

        super().__init__()

    def upgrade(self):
        all_run_ids = self.get_all_run_ids()
        print(  # pylint: disable=print-call
            f"Updating event log storage for {len(all_run_ids)} runs on disk..."
        )
        alembic_config = get_alembic_config(__file__)
        if all_run_ids:
            for run_id in tqdm(all_run_ids):
                with self.run_connection(run_id) as conn:
                    run_alembic_upgrade(alembic_config, conn, run_id)

        print("Updating event log storage for index db on disk...")  # pylint: disable=print-call
        with self.index_connection() as conn:
            run_alembic_upgrade(alembic_config, conn, "index")

        self._initialized_dbs = set()

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {"base_dir": StringSource}

    @staticmethod
    def from_config_value(inst_data, config_value):
        return SqliteEventLogStorage(inst_data=inst_data, **config_value)

    def get_all_run_ids(self):
        all_filenames = glob.glob(os.path.join(self._base_dir, "*.db"))
        return [
            os.path.splitext(os.path.basename(filename))[0]
            for filename in all_filenames
            if os.path.splitext(os.path.basename(filename))[0] != INDEX_SHARD_NAME
        ]

    def path_for_shard(self, run_id):
        return os.path.join(self._base_dir, "{run_id}.db".format(run_id=run_id))

    def conn_string_for_shard(self, shard_name):
        check.str_param(shard_name, "shard_name")
        return create_db_conn_string(self._base_dir, shard_name)

    def _initdb(self, engine):
        alembic_config = get_alembic_config(__file__)

        retry_limit = 10

        while True:
            try:

                with engine.connect() as connection:
                    db_revision, head_revision = check_alembic_revision(alembic_config, connection)

                    if not (db_revision and head_revision):
                        SqlEventLogStorageMetadata.create_all(engine)
                        engine.execute("PRAGMA journal_mode=WAL;")
                        stamp_alembic_rev(alembic_config, connection)

                break
            except (db.exc.DatabaseError, sqlite3.DatabaseError, sqlite3.OperationalError) as exc:
                # This is SQLite-specific handling for concurrency issues that can arise when
                # multiple processes (e.g. the dagit process and user code process) contend with
                # each other to init the db. When we hit the following errors, we know that another
                # process is on the case and we should retry.
                err_msg = str(exc)

                if not (
                    "table asset_keys already exists" in err_msg
                    or "table secondary_indexes already exists" in err_msg
                    or "table event_logs already exists" in err_msg
                    or "database is locked" in err_msg
                    or "table alembic_version already exists" in err_msg
                    or "UNIQUE constraint failed: alembic_version.version_num" in err_msg
                ):
                    raise

                if retry_limit == 0:
                    raise
                else:
                    logging.info(
                        "SqliteEventLogStorage._initdb: Encountered apparent concurrent init, "
                        "retrying (%s retries left). Exception: %s",
                        retry_limit,
                        err_msg,
                    )
                    time.sleep(0.2)
                    retry_limit -= 1

    @contextmanager
    def _connect(self, shard):
        with self._db_lock:
            check.str_param(shard, "shard")

            conn_string = self.conn_string_for_shard(shard)
            engine = create_engine(conn_string, poolclass=NullPool)

            if not shard in self._initialized_dbs:
                self._initdb(engine)
                self._initialized_dbs.add(shard)

            conn = engine.connect()

            try:
                yield conn
            finally:
                conn.close()
            engine.dispose()

    def run_connection(self, run_id=None):
        return self._connect(run_id)

    def index_connection(self):
        return self._connect(INDEX_SHARD_NAME)

    def store_event(self, event):
        """
        Overridden method to replicate asset events in a central assets.db sqlite shard, enabling
        cross-run asset queries.

        Args:
            event (EventLogEntry): The event to store.
        """
        check.inst_param(event, "event", EventLogEntry)
        insert_event_statement = self.prepare_insert_event(event)
        run_id = event.run_id

        with self.run_connection(run_id) as conn:
            conn.execute(insert_event_statement)

        if event.is_dagster_event and event.dagster_event.asset_key:
            check.invariant(
                event.dagster_event_type == DagsterEventType.ASSET_MATERIALIZATION
                or event.dagster_event_type == DagsterEventType.ASSET_OBSERVATION
                or event.dagster_event_type == DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
                "Can only store asset materializations, materialization_planned, and observations in index database",
            )

            # mirror the event in the cross-run index database
            with self.index_connection() as conn:
                conn.execute(insert_event_statement)

            if (
                event.dagster_event.is_step_materialization
                or event.dagster_event.is_asset_observation
                or event.dagster_event.is_asset_materialization_planned
            ):
                self.store_asset_event(event)

    def get_event_records(
        self,
        event_records_filter: Optional[EventRecordsFilter] = None,
        limit: Optional[int] = None,
        ascending: bool = False,
    ) -> Iterable[EventLogRecord]:
        """Overridden method to enable cross-run event queries in sqlite.

        The record id in sqlite does not auto increment cross runs, so instead of fetching events
        after record id, we only fetch events whose runs updated after update_timestamp.
        """
        check.opt_inst_param(event_records_filter, "event_records_filter", EventRecordsFilter)
        check.opt_int_param(limit, "limit")
        check.bool_param(ascending, "ascending")

        is_asset_query = event_records_filter and (
            event_records_filter.event_type == DagsterEventType.ASSET_MATERIALIZATION
            or event_records_filter.event_type == DagsterEventType.ASSET_OBSERVATION
        )
        if is_asset_query:
            # asset materializations and observations get mirrored into the index shard, so no
            # custom run shard-aware cursor logic needed
            return super(SqliteEventLogStorage, self).get_event_records(
                event_records_filter=event_records_filter, limit=limit, ascending=ascending
            )

        query = db.select([SqlEventLogStorageTable.c.id, SqlEventLogStorageTable.c.event])
        if event_records_filter and event_records_filter.asset_key:
            asset_details = next(iter(self._get_assets_details([event_records_filter.asset_key])))
        else:
            asset_details = None

        if not event_records_filter or not (
            isinstance(event_records_filter.after_cursor, RunShardedEventsCursor)
        ):
            warnings.warn(
                """
                Called `get_event_records` on a run-sharded event log storage with a query that
                is not run aware (e.g. not using a RunShardedEventsCursor).  This likely has poor
                performance characteristics.  Consider adding a RunShardedEventsCursor to your query
                or switching your instance configuration to use a non-run sharded event log storage
                (e.g. PostgresEventLogStorage, ConsolidatedSqliteEventLogStorage)
            """
            )

        query = self._apply_filter_to_query(
            query=query,
            event_records_filter=event_records_filter,
            asset_details=asset_details,
            apply_cursor_filters=False,  # run-sharded cursor filters don't really make sense
        )
        if limit:
            query = query.limit(limit)
        if ascending:
            query = query.order_by(SqlEventLogStorageTable.c.timestamp.asc())
        else:
            query = query.order_by(SqlEventLogStorageTable.c.timestamp.desc())

        # workaround for the run-shard sqlite to enable cross-run queries: get a list of run_ids
        # whose events may qualify the query, and then open run_connection per run_id at a time.
        run_updated_after = (
            event_records_filter.after_cursor.run_updated_after
            if event_records_filter
            and isinstance(event_records_filter.after_cursor, RunShardedEventsCursor)
            else None
        )
        run_records = self._instance.get_run_records(
            filters=RunsFilter(updated_after=run_updated_after),
            order_by="update_timestamp",
            ascending=ascending,
        )

        event_records = []
        for run_record in run_records:
            run_id = run_record.pipeline_run.run_id
            with self.run_connection(run_id) as conn:
                results = conn.execute(query).fetchall()

            for row_id, json_str in results:
                try:
                    event_record = deserialize_json_to_dagster_namedtuple(json_str)
                    if not isinstance(event_record, EventLogEntry):
                        logging.warning(
                            "Could not resolve event record as EventLogEntry for id `%s`.", row_id
                        )
                        continue
                    else:
                        event_records.append(
                            EventLogRecord(storage_id=row_id, event_log_entry=event_record)
                        )
                    if limit and len(event_records) >= limit:
                        break
                except seven.JSONDecodeError:
                    logging.warning("Could not parse event record id `%s`.", row_id)

            if limit and len(event_records) >= limit:
                break

        return event_records[:limit]

    def delete_events(self, run_id):
        with self.run_connection(run_id) as conn:
            self.delete_events_for_run(conn, run_id)

        # delete the mirrored event in the cross-run index database
        with self.index_connection() as conn:
            self.delete_events_for_run(conn, run_id)

    def wipe(self):
        # should delete all the run-sharded dbs as well as the index db
        for filename in (
            glob.glob(os.path.join(self._base_dir, "*.db"))
            + glob.glob(os.path.join(self._base_dir, "*.db-wal"))
            + glob.glob(os.path.join(self._base_dir, "*.db-shm"))
        ):
            os.unlink(filename)

        self._initialized_dbs = set()

    def _delete_mirrored_events_for_asset_key(self, asset_key):
        with self.index_connection() as conn:
            conn.execute(
                SqlEventLogStorageTable.delete().where(  # pylint: disable=no-value-for-parameter
                    db.or_(
                        SqlEventLogStorageTable.c.asset_key == asset_key.to_string(),
                        SqlEventLogStorageTable.c.asset_key == asset_key.to_string(legacy=True),
                    )
                )
            )

    def wipe_asset(self, asset_key):
        # default implementation will update the event_logs in the sharded dbs, and the asset_key
        # table in the asset shard, but will not remove the mirrored event_log events in the asset
        # shard
        super(SqliteEventLogStorage, self).wipe_asset(asset_key)
        self._delete_mirrored_events_for_asset_key(asset_key)

    def watch(self, run_id, start_cursor, callback):
        if not self._obs:
            self._obs = Observer()
            self._obs.start()

        watchdog = SqliteEventLogStorageWatchdog(self, run_id, callback, start_cursor)
        self._watchers[run_id][callback] = (
            watchdog,
            self._obs.schedule(watchdog, self._base_dir, True),
        )

    def end_watch(self, run_id, handler):
        if handler in self._watchers[run_id]:
            event_handler, watch = self._watchers[run_id][handler]
            self._obs.remove_handler_for_watch(event_handler, watch)
            del self._watchers[run_id][handler]

    def dispose(self):
        if self._obs:
            self._obs.stop()
            self._obs.join(timeout=15)

    def alembic_version(self):
        alembic_config = get_alembic_config(__file__)
        with self.index_connection() as conn:
            return check_alembic_revision(alembic_config, conn)


class SqliteEventLogStorageWatchdog(PatternMatchingEventHandler):
    def __init__(self, event_log_storage, run_id, callback, start_cursor, **kwargs):
        self._event_log_storage = check.inst_param(
            event_log_storage, "event_log_storage", SqliteEventLogStorage
        )
        self._run_id = check.str_param(run_id, "run_id")
        self._cb = check.callable_param(callback, "callback")
        self._log_path = event_log_storage.path_for_shard(run_id)
        self._cursor = start_cursor if start_cursor is not None else -1
        super(SqliteEventLogStorageWatchdog, self).__init__(patterns=[self._log_path], **kwargs)

    def _process_log(self):
        events = self._event_log_storage.get_logs_for_run(self._run_id, self._cursor)
        self._cursor += len(events)
        for event in events:
            status = None
            try:
                status = self._cb(event)
            except Exception:
                logging.exception("Exception in callback for event watch on run %s.", self._run_id)

            if (
                status == PipelineRunStatus.SUCCESS
                or status == PipelineRunStatus.FAILURE
                or status == PipelineRunStatus.CANCELED
            ):
                self._event_log_storage.end_watch(self._run_id, self._cb)

    def on_modified(self, event):
        check.invariant(event.src_path == self._log_path)
        self._process_log()
