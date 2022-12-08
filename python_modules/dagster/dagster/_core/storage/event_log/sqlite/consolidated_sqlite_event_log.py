import logging
import os
from collections import defaultdict
from contextlib import contextmanager

from sqlalchemy.pool import NullPool
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

import dagster._check as check
from dagster._config import StringSource
from dagster._core.storage.event_log.base import EventLogCursor
from dagster._core.storage.pipeline_run import DagsterRunStatus
from dagster._core.storage.sql import (
    check_alembic_revision,
    create_engine,
    get_alembic_config,
    run_alembic_upgrade,
    stamp_alembic_rev,
)
from dagster._core.storage.sqlite import create_db_conn_string
from dagster._serdes import ConfigurableClass, ConfigurableClassData
from dagster._utils import mkdir_p

from ..schema import SqlEventLogStorageMetadata
from ..sql_event_log import SqlEventLogStorage

SQLITE_EVENT_LOG_FILENAME = "event_log"


class ConsolidatedSqliteEventLogStorage(SqlEventLogStorage, ConfigurableClass):
    """SQLite-backed consolidated event log storage intended for test cases only.

    Users should not directly instantiate this class; it is instantiated by internal machinery when
    ``dagit`` and ``dagster-graphql`` load, based on the values in the ``dagster.yaml`` file in
    ``$DAGSTER_HOME``. Configuration of this class should be done by setting values in that file.

    To explicitly specify the consolidated SQLite for event log storage, you can add a block such as
    the following to your ``dagster.yaml``:

    .. code-block:: YAML

        run_storage:
          module: dagster._core.storage.event_log
          class: ConsolidatedSqliteEventLogStorage
          config:
            base_dir: /path/to/dir

    The ``base_dir`` param tells the event log storage where on disk to store the database.
    """

    def __init__(self, base_dir, inst_data=None):
        self._base_dir = check.str_param(base_dir, "base_dir")
        self._conn_string = create_db_conn_string(base_dir, SQLITE_EVENT_LOG_FILENAME)
        self._secondary_index_cache = {}
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self._watchers = defaultdict(dict)
        self._obs = None

        if not os.path.exists(self.get_db_path()):
            self._init_db()

        super().__init__()

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {"base_dir": StringSource}

    @staticmethod
    def from_config_value(inst_data, config_value):
        return ConsolidatedSqliteEventLogStorage(inst_data=inst_data, **config_value)

    def _init_db(self):
        mkdir_p(self._base_dir)
        engine = create_engine(self._conn_string, poolclass=NullPool)
        alembic_config = get_alembic_config(__file__)

        should_mark_indexes = False
        with engine.connect() as connection:
            db_revision, head_revision = check_alembic_revision(alembic_config, connection)
            if not (db_revision and head_revision):
                SqlEventLogStorageMetadata.create_all(engine)
                engine.execute("PRAGMA journal_mode=WAL;")
                stamp_alembic_rev(alembic_config, connection)
                should_mark_indexes = True

        if should_mark_indexes:
            # mark all secondary indexes
            self.reindex_events()
            self.reindex_assets()

    @contextmanager
    def _connect(self):
        engine = create_engine(self._conn_string, poolclass=NullPool)
        conn = engine.connect()
        try:
            yield conn
        finally:
            conn.close()

    def run_connection(self, run_id):
        return self._connect()

    def index_connection(self):
        return self._connect()

    def has_table(self, table_name: str) -> bool:
        engine = create_engine(self._conn_string, poolclass=NullPool)
        return bool(engine.dialect.has_table(engine.connect(), table_name))

    def get_db_path(self):
        return os.path.join(self._base_dir, "{}.db".format(SQLITE_EVENT_LOG_FILENAME))

    def upgrade(self):
        alembic_config = get_alembic_config(__file__)
        with self._connect() as conn:
            run_alembic_upgrade(alembic_config, conn)

    def has_secondary_index(self, name):
        if name not in self._secondary_index_cache:
            self._secondary_index_cache[name] = super(
                ConsolidatedSqliteEventLogStorage, self
            ).has_secondary_index(name)
        return self._secondary_index_cache[name]

    def enable_secondary_index(self, name):
        super(ConsolidatedSqliteEventLogStorage, self).enable_secondary_index(name)
        if name in self._secondary_index_cache:
            del self._secondary_index_cache[name]

    def watch(self, run_id, cursor, callback):
        if not self._obs:
            self._obs = Observer()
            self._obs.start()
            self._obs.schedule(
                ConsolidatedSqliteEventLogStorageWatchdog(self), self._base_dir, True
            )

        self._watchers[run_id][callback] = cursor

    def on_modified(self):
        keys = [
            (run_id, callback)
            for run_id, callback_dict in self._watchers.items()
            for callback, _ in callback_dict.items()
        ]
        for run_id, callback in keys:
            cursor = self._watchers[run_id][callback]

            # fetch events
            connection = self.get_records_for_run(run_id, cursor)

            # update cursor
            if connection.cursor:
                self._watchers[run_id][callback] = connection.cursor

            for record in connection.records:
                status = None
                try:
                    status = callback(
                        record.event_log_entry,
                        str(EventLogCursor.from_storage_id(record.storage_id)),
                    )
                except Exception:
                    logging.exception("Exception in callback for event watch on run %s.", run_id)

                if (
                    status == DagsterRunStatus.SUCCESS
                    or status == DagsterRunStatus.FAILURE
                    or status == DagsterRunStatus.CANCELED
                ):
                    self.end_watch(run_id, callback)

    def end_watch(self, run_id, handler):
        if run_id in self._watchers and handler in self._watchers[run_id]:
            del self._watchers[run_id][handler]

    def dispose(self):
        if self._obs:
            self._obs.stop()
            self._obs.join(timeout=15)


class ConsolidatedSqliteEventLogStorageWatchdog(PatternMatchingEventHandler):
    def __init__(self, event_log_storage, **kwargs):
        self._event_log_storage = check.inst_param(
            event_log_storage, "event_log_storage", ConsolidatedSqliteEventLogStorage
        )
        self._log_path = event_log_storage.get_db_path()
        super(ConsolidatedSqliteEventLogStorageWatchdog, self).__init__(
            patterns=[self._log_path], **kwargs
        )

    def on_modified(self, event):
        check.invariant(event.src_path == self._log_path)
        self._event_log_storage.on_modified()
