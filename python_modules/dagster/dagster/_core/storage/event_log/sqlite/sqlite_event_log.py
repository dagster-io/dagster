import contextlib
import glob
import logging
import os
import re
import sqlite3
import threading
import time
from collections import defaultdict
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, ContextManager, Iterable, Iterator, Optional, Sequence

import sqlalchemy as db
import sqlalchemy.exc as db_exc
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.pool import NullPool
from tqdm import tqdm
from watchdog.events import FileSystemEvent, PatternMatchingEventHandler
from watchdog.observers import Observer

import dagster._check as check
import dagster._seven as seven
from dagster._config import StringSource
from dagster._config.config_schema import UserConfigSchema
from dagster._core.definitions.events import AssetKey
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.event_api import EventHandlerFn
from dagster._core.events import ASSET_EVENTS
from dagster._core.events.log import EventLogEntry
from dagster._core.storage.dagster_run import DagsterRunStatus, RunsFilter
from dagster._core.storage.event_log.base import EventLogCursor, EventLogRecord, EventRecordsFilter
from dagster._core.storage.sql import (
    AlembicVersion,
    check_alembic_revision,
    create_engine,
    get_alembic_config,
    run_alembic_upgrade,
    stamp_alembic_rev,
)
from dagster._core.storage.sqlalchemy_compat import db_select
from dagster._core.storage.sqlite import create_db_conn_string
from dagster._serdes import (
    ConfigurableClass,
    ConfigurableClassData,
)
from dagster._serdes.errors import DeserializationError
from dagster._serdes.serdes import deserialize_value
from dagster._utils import mkdir_p

from ..schema import SqlEventLogStorageMetadata, SqlEventLogStorageTable
from ..sql_event_log import RunShardedEventsCursor, SqlEventLogStorage

if TYPE_CHECKING:
    from dagster._core.storage.sqlite_storage import SqliteStorageConfig
INDEX_SHARD_NAME = "index"


class SqliteEventLogStorage(SqlEventLogStorage, ConfigurableClass):
    """SQLite-backed event log storage.

    Users should not directly instantiate this class; it is instantiated by internal machinery when
    ``dagster-webserver`` and ``dagster-graphql`` load, based on the values in the ``dagster.yaml`` file insqliteve
    ``$DAGSTER_HOME``. Configuration of this class should be done by setting values in that file.

    This is the default event log storage when none is specified in the ``dagster.yaml``.

    To explicitly specify SQLite for event log storage, you can add a block such as the following
    to your ``dagster.yaml``:

    .. code-block:: YAML

        event_log_storage:
          module: dagster._core.storage.event_log
          class: SqliteEventLogStorage
          config:
            base_dir: /path/to/dir

    The ``base_dir`` param tells the event log storage where on disk to store the databases. To
    improve concurrent performance, event logs are stored in a separate SQLite database for each
    run.
    """

    def __init__(self, base_dir: str, inst_data: Optional[ConfigurableClassData] = None):
        """Note that idempotent initialization of the SQLite database is done on a per-run_id
        basis in the body of connect, since each run is stored in a separate database.
        """
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

    def upgrade(self) -> None:
        all_run_ids = self.get_all_run_ids()
        print(f"Updating event log storage for {len(all_run_ids)} runs on disk...")  # noqa: T201
        alembic_config = get_alembic_config(__file__)
        if all_run_ids:
            for run_id in tqdm(all_run_ids):
                with self.run_connection(run_id) as conn:
                    run_alembic_upgrade(alembic_config, conn, run_id)

        print("Updating event log storage for index db on disk...")  # noqa: T201
        with self.index_connection() as conn:
            run_alembic_upgrade(alembic_config, conn, "index")

        self._initialized_dbs = set()

    @property
    def inst_data(self) -> Optional[ConfigurableClassData]:
        return self._inst_data

    @classmethod
    def config_type(cls) -> UserConfigSchema:
        return {"base_dir": StringSource}

    @classmethod
    def from_config_value(
        cls, inst_data: Optional[ConfigurableClassData], config_value: "SqliteStorageConfig"
    ) -> "SqliteEventLogStorage":
        return SqliteEventLogStorage(inst_data=inst_data, **config_value)

    def get_all_run_ids(self) -> Sequence[str]:
        all_filenames = glob.glob(os.path.join(self._base_dir, "*.db"))
        return [
            os.path.splitext(os.path.basename(filename))[0]
            for filename in all_filenames
            if os.path.splitext(os.path.basename(filename))[0] != INDEX_SHARD_NAME
        ]

    def has_table(self, table_name: str) -> bool:
        conn_string = self.conn_string_for_shard(INDEX_SHARD_NAME)
        engine = create_engine(conn_string, poolclass=NullPool)
        with engine.connect() as conn:
            return bool(engine.dialect.has_table(conn, table_name))

    def path_for_shard(self, run_id: str) -> str:
        return os.path.join(self._base_dir, f"{run_id}.db")

    def conn_string_for_shard(self, shard_name: str) -> str:
        check.str_param(shard_name, "shard_name")
        return create_db_conn_string(self._base_dir, shard_name)

    def _initdb(self, engine: Engine) -> None:
        alembic_config = get_alembic_config(__file__)

        retry_limit = 10

        while True:
            try:
                with engine.connect() as connection:
                    db_revision, head_revision = check_alembic_revision(alembic_config, connection)

                    if not (db_revision and head_revision):
                        SqlEventLogStorageMetadata.create_all(engine)
                        connection.execute(db.text("PRAGMA journal_mode=WAL;"))
                        stamp_alembic_rev(alembic_config, connection)

                break
            except (db_exc.DatabaseError, sqlite3.DatabaseError, sqlite3.OperationalError) as exc:
                # This is SQLite-specific handling for concurrency issues that can arise when
                # multiple processes (e.g. the dagster-webserver process and user code process) contend with
                # each other to init the db. When we hit the following errors, we know that another
                # process is on the case and we should retry.
                err_msg = str(exc)

                if not (
                    re.search(r"table [A-Za-z_]* already exists", err_msg)
                    or "database is locked" in err_msg
                    or "UNIQUE constraint failed: alembic_version.version_num" in err_msg
                ):
                    raise

                if retry_limit == 0:
                    raise
                else:
                    logging.info(
                        (
                            "SqliteEventLogStorage._initdb: Encountered apparent concurrent init, "
                            "retrying (%s retries left). Exception: %s"
                        ),
                        retry_limit,
                        err_msg,
                    )
                    time.sleep(0.2)
                    retry_limit -= 1

    @contextmanager
    def _connect(self, shard: str) -> Iterator[Connection]:
        with self._db_lock:
            check.str_param(shard, "shard")

            conn_string = self.conn_string_for_shard(shard)
            engine = create_engine(conn_string, poolclass=NullPool)

            if shard not in self._initialized_dbs:
                self._initdb(engine)
                self._initialized_dbs.add(shard)

            with engine.connect() as conn:
                with conn.begin():
                    yield conn
            engine.dispose()

    def run_connection(self, run_id: Optional[str] = None) -> Any:
        return self._connect(run_id)  # type: ignore  # bad sig

    def index_connection(self) -> ContextManager[Connection]:
        return self._connect(INDEX_SHARD_NAME)

    def store_event(self, event: EventLogEntry) -> None:
        """Overridden method to replicate asset events in a central assets.db sqlite shard, enabling
        cross-run asset queries.

        Args:
            event (EventLogEntry): The event to store.
        """
        check.inst_param(event, "event", EventLogEntry)
        insert_event_statement = self.prepare_insert_event(event)
        run_id = event.run_id

        with self.run_connection(run_id) as conn:
            conn.execute(insert_event_statement)

        if event.is_dagster_event and event.dagster_event.asset_key:  # type: ignore
            check.invariant(
                event.dagster_event_type in ASSET_EVENTS,
                (
                    "Can only store asset materializations, materialization_planned, and"
                    " observations in index database"
                ),
            )

            event_id = None

            # mirror the event in the cross-run index database
            with self.index_connection() as conn:
                result = conn.execute(insert_event_statement)
                event_id = result.inserted_primary_key[0]

            self.store_asset_event(event, event_id)

            if event_id is None:
                raise DagsterInvariantViolationError(
                    "Cannot store asset event tags for null event id."
                )

            self.store_asset_event_tags(event, event_id)

    def get_event_records(
        self,
        event_records_filter: EventRecordsFilter,
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

        is_asset_query = event_records_filter and event_records_filter.event_type in ASSET_EVENTS
        if is_asset_query:
            # asset materializations, observations and materialization planned events
            # get mirrored into the index shard, so no custom run shard-aware cursor logic needed
            return super(SqliteEventLogStorage, self).get_event_records(
                event_records_filter=event_records_filter, limit=limit, ascending=ascending
            )

        query = db_select([SqlEventLogStorageTable.c.id, SqlEventLogStorageTable.c.event])
        if event_records_filter.asset_key:
            asset_details = next(iter(self._get_assets_details([event_records_filter.asset_key])))
        else:
            asset_details = None

        if event_records_filter.after_cursor is not None and not isinstance(
            event_records_filter.after_cursor, RunShardedEventsCursor
        ):
            raise Exception(
                """
                Called `get_event_records` on a run-sharded event log storage with a cursor that
                is not run-aware. Add a RunShardedEventsCursor to your query filter
                or switch your instance configuration to use a non-run-sharded event log storage
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
            if isinstance(event_records_filter.after_cursor, RunShardedEventsCursor)
            else None
        )
        run_records = self._instance.get_run_records(
            filters=RunsFilter(updated_after=run_updated_after),
            order_by="update_timestamp",
            ascending=ascending,
        )

        event_records = []
        for run_record in run_records:
            run_id = run_record.dagster_run.run_id
            with self.run_connection(run_id) as conn:
                results = conn.execute(query).fetchall()

            for row_id, json_str in results:
                try:
                    event_record = deserialize_value(json_str, EventLogEntry)
                    event_records.append(
                        EventLogRecord(storage_id=row_id, event_log_entry=event_record)
                    )
                    if limit and len(event_records) >= limit:
                        break
                except DeserializationError:
                    logging.warning(
                        "Could not resolve event record as EventLogEntry for id `%s`.", row_id
                    )
                except seven.JSONDecodeError:
                    logging.warning("Could not parse event record id `%s`.", row_id)

            if limit and len(event_records) >= limit:
                break

        return event_records[:limit]

    def supports_event_consumer_queries(self) -> bool:
        return False

    def delete_events(self, run_id: str) -> None:
        with self.run_connection(run_id) as conn:
            self.delete_events_for_run(conn, run_id)

        # delete the mirrored event in the cross-run index database
        with self.index_connection() as conn:
            self.delete_events_for_run(conn, run_id)

    def wipe(self) -> None:
        # should delete all the run-sharded db files and drop the contents of the index
        for filename in (
            glob.glob(os.path.join(self._base_dir, "*.db"))
            + glob.glob(os.path.join(self._base_dir, "*.db-wal"))
            + glob.glob(os.path.join(self._base_dir, "*.db-shm"))
        ):
            if (
                not filename.endswith(f"{INDEX_SHARD_NAME}.db")
                and not filename.endswith(f"{INDEX_SHARD_NAME}.db-wal")
                and not filename.endswith(f"{INDEX_SHARD_NAME}.db-shm")
            ):
                with contextlib.suppress(FileNotFoundError):
                    os.unlink(filename)

        self._initialized_dbs = set()
        self._wipe_index()

    def _delete_mirrored_events_for_asset_key(self, asset_key: AssetKey) -> None:
        with self.index_connection() as conn:
            conn.execute(
                SqlEventLogStorageTable.delete().where(
                    SqlEventLogStorageTable.c.asset_key == asset_key.to_string(),
                )
            )

    def wipe_asset(self, asset_key: AssetKey) -> None:
        # default implementation will update the event_logs in the sharded dbs, and the asset_key
        # table in the asset shard, but will not remove the mirrored event_log events in the asset
        # shard
        super(SqliteEventLogStorage, self).wipe_asset(asset_key)
        self._delete_mirrored_events_for_asset_key(asset_key)

    def watch(self, run_id: str, cursor: Optional[str], callback: EventHandlerFn) -> None:
        if not self._obs:
            self._obs = Observer()
            self._obs.start()

        watchdog = SqliteEventLogStorageWatchdog(self, run_id, callback, cursor)
        self._watchers[run_id][callback] = (
            watchdog,
            self._obs.schedule(watchdog, self._base_dir, True),
        )

    def end_watch(self, run_id: str, handler: EventHandlerFn) -> None:
        if handler in self._watchers[run_id]:
            event_handler, watch = self._watchers[run_id][handler]
            self._obs.remove_handler_for_watch(event_handler, watch)  # type: ignore  # (possible none)
            del self._watchers[run_id][handler]

    def dispose(self) -> None:
        if self._obs:
            self._obs.stop()
            self._obs.join(timeout=15)

    def alembic_version(self) -> AlembicVersion:
        alembic_config = get_alembic_config(__file__)
        with self.index_connection() as conn:
            return check_alembic_revision(alembic_config, conn)

    @property
    def is_run_sharded(self) -> bool:
        return True

    @property
    def supports_global_concurrency_limits(self) -> bool:
        return False


class SqliteEventLogStorageWatchdog(PatternMatchingEventHandler):
    def __init__(
        self,
        event_log_storage: SqliteEventLogStorage,
        run_id: str,
        callback: EventHandlerFn,
        cursor: Optional[str],
        **kwargs: Any,
    ):
        self._event_log_storage = check.inst_param(
            event_log_storage, "event_log_storage", SqliteEventLogStorage
        )
        self._run_id = check.str_param(run_id, "run_id")
        self._cb = check.callable_param(callback, "callback")
        self._log_path = event_log_storage.path_for_shard(run_id)
        self._cursor = cursor
        super(SqliteEventLogStorageWatchdog, self).__init__(patterns=[self._log_path], **kwargs)

    def _process_log(self) -> None:
        connection = self._event_log_storage.get_records_for_run(self._run_id, self._cursor)
        if connection.cursor:
            self._cursor = connection.cursor
        for record in connection.records:
            status = None
            try:
                status = self._cb(
                    record.event_log_entry, str(EventLogCursor.from_storage_id(record.storage_id))
                )
            except Exception:
                logging.exception("Exception in callback for event watch on run %s.", self._run_id)

            if (
                status == DagsterRunStatus.SUCCESS
                or status == DagsterRunStatus.FAILURE
                or status == DagsterRunStatus.CANCELED
            ):
                self._event_log_storage.end_watch(self._run_id, self._cb)

    def on_modified(self, event: FileSystemEvent) -> None:
        check.invariant(event.src_path == self._log_path)
        self._process_log()
