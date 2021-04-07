import threading
from collections import defaultdict
from typing import Callable, List, MutableMapping, Optional

import psycopg2
import sqlalchemy as db
from dagster import check
from dagster.core.events.log import EventRecord
from dagster.core.storage.event_log import (
    AssetKeyTable,
    SqlEventLogStorage,
    SqlEventLogStorageMetadata,
    SqlEventLogStorageTable,
)
from dagster.core.storage.event_log.polling_event_watcher import CallbackAfterCursor
from dagster.core.storage.sql import create_engine, run_alembic_upgrade, stamp_alembic_rev
from dagster.serdes import (
    ConfigurableClass,
    ConfigurableClassData,
    deserialize_json_to_dagster_namedtuple,
    serialize_dagster_namedtuple,
)

from ..pynotify import await_pg_notifications
from ..utils import (
    create_pg_connection,
    pg_alembic_config,
    pg_config,
    pg_statement_timeout,
    pg_url_from_config,
    retry_pg_connection_fn,
    retry_pg_creation_fn,
)

CHANNEL_NAME = "run_events"


class PostgresEventLogStorage(SqlEventLogStorage, ConfigurableClass):
    """Postgres-backed event log storage.

    Users should not directly instantiate this class; it is instantiated by internal machinery when
    ``dagit`` and ``dagster-graphql`` load, based on the values in the ``dagster.yaml`` file in
    ``$DAGSTER_HOME``. Configuration of this class should be done by setting values in that file.

    To use Postgres for event log storage, you can add a block such as the following to your
    ``dagster.yaml``:

    .. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/deploying/dagster-pg.yaml
       :caption: dagster.yaml
       :lines: 12-21
       :language: YAML

    Note that the fields in this config are :py:class:`~dagster.StringSource` and
    :py:class:`~dagster.IntSource` and can be configured from environment variables.

    """

    def __init__(self, postgres_url, should_autocreate_tables=True, inst_data=None):
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self.postgres_url = check.str_param(postgres_url, "postgres_url")
        self.should_autocreate_tables = check.bool_param(
            should_autocreate_tables, "should_autocreate_tables"
        )

        self._disposed = False

        self._event_watcher = PostgresEventWatcher(self.postgres_url)

        # Default to not holding any connections open to prevent accumulating connections per DagsterInstance
        self._engine = create_engine(
            self.postgres_url, isolation_level="AUTOCOMMIT", poolclass=db.pool.NullPool
        )
        self._secondary_index_cache = {}

        table_names = retry_pg_connection_fn(lambda: db.inspect(self._engine).get_table_names())

        if self.should_autocreate_tables and "event_logs" not in table_names:
            with self._connect() as conn:
                alembic_config = pg_alembic_config(__file__)
                retry_pg_creation_fn(lambda: SqlEventLogStorageMetadata.create_all(conn))

                # This revision may be shared by any other dagster storage classes using the same DB
                stamp_alembic_rev(alembic_config, conn)

            # mark all secondary indexes to be used
            self.reindex()

        super().__init__()

    def optimize_for_dagit(self, statement_timeout):
        # When running in dagit, hold an open connection and set statement_timeout
        self._engine = create_engine(
            self.postgres_url,
            isolation_level="AUTOCOMMIT",
            pool_size=1,
            connect_args={"options": pg_statement_timeout(statement_timeout)},
        )

    def upgrade(self):
        alembic_config = pg_alembic_config(__file__)
        with self._connect() as conn:
            run_alembic_upgrade(alembic_config, conn)

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return pg_config()

    @staticmethod
    def from_config_value(inst_data, config_value):
        return PostgresEventLogStorage(
            inst_data=inst_data,
            postgres_url=pg_url_from_config(config_value),
            should_autocreate_tables=config_value.get("should_autocreate_tables", True),
        )

    @staticmethod
    def create_clean_storage(conn_string, should_autocreate_tables=True):
        engine = create_engine(
            conn_string, isolation_level="AUTOCOMMIT", poolclass=db.pool.NullPool
        )
        try:
            SqlEventLogStorageMetadata.drop_all(engine)
        finally:
            engine.dispose()

        return PostgresEventLogStorage(conn_string, should_autocreate_tables)

    def store_event(self, event):
        """Store an event corresponding to a pipeline run.
        Args:
            event (EventRecord): The event to store.
        """
        check.inst_param(event, "event", EventRecord)
        insert_event_statement = self.prepare_insert_event(event)  # from SqlEventLogStorage.py
        with self._connect() as conn:
            result = conn.execute(
                insert_event_statement.returning(
                    SqlEventLogStorageTable.c.run_id, SqlEventLogStorageTable.c.id
                )
            )
            res = result.fetchone()
            result.close()
            conn.execute(
                """NOTIFY {channel}, %s; """.format(channel=CHANNEL_NAME),
                (res[0] + "_" + str(res[1]),),
            )

        if event.is_dagster_event and event.dagster_event.asset_key:
            self.store_asset(event)

    def store_asset(self, event):
        check.inst_param(event, "event", EventRecord)
        if not event.is_dagster_event or not event.dagster_event.asset_key:
            return

        materialization = event.dagster_event.step_materialization_data.materialization
        with self.index_connection() as conn:
            conn.execute(
                db.dialects.postgresql.insert(AssetKeyTable)
                .values(
                    asset_key=event.dagster_event.asset_key.to_string(),
                    last_materialization=serialize_dagster_namedtuple(materialization),
                    last_run_id=event.run_id,
                )
                .on_conflict_do_update(
                    index_elements=[AssetKeyTable.c.asset_key],
                    set_=dict(
                        last_materialization=serialize_dagster_namedtuple(materialization),
                        last_run_id=event.run_id,
                    ),
                )
            )

    def _connect(self):
        return create_pg_connection(self._engine, __file__, "event log")

    def run_connection(self, run_id=None):
        return self._connect()

    def index_connection(self):
        return self._connect()

    def has_secondary_index(self, name):
        if name not in self._secondary_index_cache:
            self._secondary_index_cache[name] = super(
                PostgresEventLogStorage, self
            ).has_secondary_index(name)
        return self._secondary_index_cache[name]

    def enable_secondary_index(self, name):
        super(PostgresEventLogStorage, self).enable_secondary_index(name)
        if name in self._secondary_index_cache:
            del self._secondary_index_cache[name]

    def watch(self, run_id, start_cursor, callback):
        self._event_watcher.watch_run(run_id, start_cursor, callback)

    def end_watch(self, run_id, handler):
        self._event_watcher.unwatch_run(run_id, handler)

    @property
    def event_watcher(self):
        return self._event_watcher

    def __del__(self):
        # Keep the inherent limitations of __del__ in Python in mind!
        self.dispose()

    def dispose(self):
        if not self._disposed:
            self._disposed = True
            self._event_watcher.close()


POLLING_CADENCE = 0.25


def watcher_thread(
    conn_string: str,
    handlers_dict: MutableMapping[str, List[CallbackAfterCursor]],
    dict_lock: threading.Lock,
    watcher_thread_exit: threading.Event,
    watcher_thread_started: threading.Event,
):
    try:
        for notif in await_pg_notifications(
            conn_string,
            channels=[CHANNEL_NAME],
            timeout=POLLING_CADENCE,
            yield_on_timeout=True,
            exit_event=watcher_thread_exit,
            started_event=watcher_thread_started,
        ):
            if not isinstance(notif, psycopg2.extensions.Notify):
                if watcher_thread_exit.is_set():
                    break
            else:
                run_id, index_str = notif.payload.split("_")
                with dict_lock:
                    if run_id not in handlers_dict:
                        continue

                index = int(index_str)
                with dict_lock:
                    handlers = handlers_dict.get(run_id, [])

                engine = create_engine(
                    conn_string, isolation_level="AUTOCOMMIT", poolclass=db.pool.NullPool
                )
                try:
                    with engine.connect() as conn:
                        # https://github.com/dagster-io/dagster/issues/3858
                        cursor_res = conn.execute(
                            db.select([SqlEventLogStorageTable.c.event]).where(
                                SqlEventLogStorageTable.c.id == index
                            ),
                        )
                        dagster_event: EventRecord = deserialize_json_to_dagster_namedtuple(
                            cursor_res.scalar()
                        )
                finally:
                    engine.dispose()

                with dict_lock:
                    for callback_with_cursor in handlers:
                        if callback_with_cursor.start_cursor < index:
                            callback_with_cursor.callback(dagster_event)
    except psycopg2.OperationalError:
        pass


class PostgresEventWatcher:
    def __init__(self, conn_string: str):
        self._conn_string: str = check.str_param(conn_string, "conn_string")
        self._handlers_dict: MutableMapping[str, List[CallbackAfterCursor]] = defaultdict(list)
        self._dict_lock: threading.Lock = threading.Lock()
        self._watcher_thread_exit: Optional[threading.Event] = None
        self._watcher_thread_started: Optional[threading.Event] = None
        self._watcher_thread: Optional[threading.Thread] = None

    def watch_run(
        self,
        run_id: str,
        start_cursor: int,
        callback: Callable[[EventRecord], None],
        start_timeout=15,
    ):
        check.str_param(run_id, "run_id")
        check.int_param(start_cursor, "start_cursor")
        check.callable_param(callback, "callback")
        if not self._watcher_thread:
            self._watcher_thread_exit = threading.Event()
            self._watcher_thread_started = threading.Event()

            self._watcher_thread = threading.Thread(
                target=watcher_thread,
                args=(
                    self._conn_string,
                    self._handlers_dict,
                    self._dict_lock,
                    self._watcher_thread_exit,
                    self._watcher_thread_started,
                ),
                name="postgres-event-watch",
            )
            self._watcher_thread.daemon = True
            self._watcher_thread.start()

            # Wait until the watcher thread is actually listening before returning
            self._watcher_thread_started.wait(start_timeout)
            if not self._watcher_thread_started.is_set():
                raise Exception("Watcher thread never started")

        with self._dict_lock:
            self._handlers_dict[run_id].append(CallbackAfterCursor(start_cursor + 1, callback))

    def unwatch_run(self, run_id: str, handler: Callable[[EventRecord], None]):
        check.str_param(run_id, "run_id")
        check.callable_param(handler, "handler")
        with self._dict_lock:
            if run_id in self._handlers_dict:
                self._handlers_dict[run_id] = [
                    callback_with_cursor
                    for callback_with_cursor in self._handlers_dict[run_id]
                    if callback_with_cursor.callback != handler
                ]
                if not self._handlers_dict[run_id]:
                    del self._handlers_dict[run_id]

    def close(self):
        if self._watcher_thread:
            self._watcher_thread_exit.set()
            self._watcher_thread.join()
            self._watcher_thread_exit = None
            self._watcher_thread = None
