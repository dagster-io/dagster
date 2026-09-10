from typing import ContextManager, cast  # noqa: UP035

import dagster._check as check
import sqlalchemy as db
import sqlalchemy.exc as db_exc
import sqlalchemy.pool as db_pool
from dagster._config.config_schema import UserConfigSchema
from dagster._core.event_api import EventHandlerFn
from dagster._core.events.log import EventLogEntry
from dagster._core.storage.config import MsSqlStorageConfig, mssql_config
from dagster._core.storage.event_log import (
    AssetKeyTable,
    SqlEventLogStorage,
    SqlEventLogStorageMetadata,
    SqlPollingEventWatcher,
)
from dagster._core.storage.event_log.base import EventLogCursor
from dagster._core.storage.event_log.migration import ASSET_KEY_INDEX_COLS
from dagster._core.storage.sql import (
    AlembicVersion,
    check_alembic_revision,
    create_engine,
    run_alembic_upgrade,
    stamp_alembic_rev,
)
from dagster._core.storage.sqlalchemy_compat import db_result
from dagster._serdes import ConfigurableClass, ConfigurableClassData
from sqlalchemy.engine import Connection

from dagster_mssql.merge import merge_statement
from dagster_mssql.utils import (
    LIKE_ESCAPE_CHAR,
    create_mssql_connection,
    mssql_alembic_config,
    mssql_isolation_level,
    mssql_url_from_config,
    retry_mssql_connection_fn,
    retry_mssql_creation_fn,
    retry_transaction,
    warn_if_read_committed_snapshot_disabled,
)


class MSSQLEventLogStorage(SqlEventLogStorage, ConfigurableClass):
    """SQL Server-backed event log storage.

    Users should not directly instantiate this class; it is instantiated by internal machinery when
    ``dagster-webserver`` and ``dagster-graphql`` load, based on the values in the ``dagster.yaml`` file in
    ``$DAGSTER_HOME``. Configuration of this class should be done by setting values in that file.

    .. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/deployment/execution/dagster-mssql-legacy.yaml
       :caption: dagster.yaml
       :start-after: start_marker_event_log
       :end-before: end_marker_event_log
       :language: YAML

    Note that the fields in this config are :py:class:`~dagster.StringSource` and
    :py:class:`~dagster.IntSource` and can be configured from environment variables.
    """

    def __init__(self, mssql_url: str, inst_data: ConfigurableClassData | None = None):
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self.mssql_url = check.str_param(mssql_url, "mssql_url")
        self._event_watcher: SqlPollingEventWatcher | None = None

        # Default to not holding any connections open to prevent accumulating connections per DagsterInstance
        self._engine = create_engine(
            self.mssql_url,
            isolation_level=mssql_isolation_level(),
            poolclass=db_pool.NullPool,
        )
        self._secondary_index_cache = {}

        table_names = retry_mssql_connection_fn(db.inspect(self._engine).get_table_names)

        # Stamp and create tables if the main table does not exist (we can't check alembic
        # revision because alembic config may be shared with other storage classes)
        if "event_logs" not in table_names:
            retry_mssql_creation_fn(self._init_db)
            # mark all secondary indexes to be used
            self.reindex_events()
            self.reindex_assets()

        self._mssql_version = self.get_server_version()
        warn_if_read_committed_snapshot_disabled(self._engine)
        super().__init__()

    def _init_db(self) -> None:
        with self._connect() as conn:
            SqlEventLogStorageMetadata.create_all(conn)
            stamp_alembic_rev(mssql_alembic_config(__file__), conn)

    def optimize_for_webserver(
        self, statement_timeout: int, pool_recycle: int, max_overflow: int
    ) -> None:
        # When running in dagster-webserver, hold an open connection
        # https://github.com/dagster-io/dagster/issues/3719
        self._engine = create_engine(
            self.mssql_url,
            isolation_level=mssql_isolation_level(),
            pool_size=1,
            pool_recycle=pool_recycle,
            max_overflow=max_overflow,
        )

    def upgrade(self) -> None:
        alembic_config = mssql_alembic_config(__file__)
        with self._connect() as conn:
            run_alembic_upgrade(alembic_config, conn)

    @property
    def inst_data(self) -> ConfigurableClassData | None:
        return self._inst_data

    @classmethod
    def config_type(cls) -> UserConfigSchema:
        return mssql_config()

    @classmethod
    def from_config_value(  # ty: ignore[invalid-method-override]
        cls, inst_data: ConfigurableClassData | None, config_value: MsSqlStorageConfig
    ) -> "MSSQLEventLogStorage":
        return MSSQLEventLogStorage(
            inst_data=inst_data, mssql_url=mssql_url_from_config(config_value)
        )

    @staticmethod
    def wipe_storage(mssql_url: str) -> None:
        engine = create_engine(
            mssql_url, isolation_level=mssql_isolation_level(), poolclass=db_pool.NullPool
        )
        try:
            SqlEventLogStorageMetadata.drop_all(engine)
        finally:
            engine.dispose()

    @staticmethod
    def create_clean_storage(conn_string: str) -> "MSSQLEventLogStorage":
        MSSQLEventLogStorage.wipe_storage(conn_string)
        return MSSQLEventLogStorage(conn_string)

    def get_server_version(self) -> str | None:
        with (
            self.index_connection() as conn,
            db_result(
                conn, db.text("SELECT CAST(SERVERPROPERTY('ProductVersion') AS VARCHAR)")
            ) as result,
        ):
            row = result.fetchone()

        if not row:
            return None

        return cast("str", row[0])

    def store_asset_event(self, event: EventLogEntry, event_id: int) -> None:
        check.inst_param(event, "event", EventLogEntry)
        check.int_param(event_id, "event_id")

        retry_transaction(
            lambda: super(MSSQLEventLogStorage, self).store_asset_event(event, event_id)
        )

    def _store_asset_event_and_tags(self, event: EventLogEntry, event_id: int) -> None:
        # Concurrent writers are chosen as deadlock victims even when materializing
        # different assets, because the upsert holds a key-range lock. Measured, not
        # assumed: test_concurrency.py::TestAssetEvents::test_distinct_asset_keys.
        retry_transaction(
            lambda: super(MSSQLEventLogStorage, self)._store_asset_event_and_tags(event, event_id)
        )

    def _store_asset_event(self, conn: Connection, event: EventLogEntry, event_id: int) -> None:
        # last_materialization_timestamp is updated upon observation, materialization, materialization_planned
        # See SqlEventLogStorage.store_asset_event method for more details

        if not (event.dagster_event and event.dagster_event.asset_key):
            return

        values = self._get_asset_entry_values(
            event, event_id, self.has_secondary_index(ASSET_KEY_INDEX_COLS)
        )
        asset_key = event.dagster_event.asset_key.to_string()
        if values:
            conn.execute(
                merge_statement(
                    AssetKeyTable,
                    match_on=["asset_key"],
                    values={"asset_key": asset_key, **values},
                )
            )
        else:
            try:
                conn.execute(AssetKeyTable.insert().values(asset_key=asset_key))
            except db_exc.IntegrityError:
                pass

    def _asset_key_startswith(self, prefix_str: str):
        # T-SQL treats `[` as the start of a character class inside a LIKE pattern, and a
        # serialized asset key always begins with one, so the unescaped pattern that works
        # everywhere else matches nothing here. SQLAlchemy's `autoescape` only covers the
        # standard metacharacters (`%` and `_`), so `[` has to be escaped explicitly.
        escaped = (
            prefix_str.replace(LIKE_ESCAPE_CHAR, LIKE_ESCAPE_CHAR * 2)
            .replace("%", f"{LIKE_ESCAPE_CHAR}%")
            .replace("_", f"{LIKE_ESCAPE_CHAR}_")
            .replace("[", f"{LIKE_ESCAPE_CHAR}[")
        )
        return AssetKeyTable.c.asset_key.like(f"{escaped}%", escape=LIKE_ESCAPE_CHAR)

    def _connect(self) -> ContextManager[Connection]:
        return create_mssql_connection(self._engine, __file__, "event log")

    def run_connection(self, run_id: str | None = None) -> ContextManager[Connection]:
        return self._connect()

    def index_connection(self) -> ContextManager[Connection]:
        return self._connect()

    def has_table(self, table_name: str) -> bool:
        with self._connect() as conn:
            return table_name in db.inspect(conn).get_table_names()

    def has_secondary_index(self, name: str) -> bool:
        if name not in self._secondary_index_cache:
            self._secondary_index_cache[name] = super().has_secondary_index(name)
        return self._secondary_index_cache[name]

    def enable_secondary_index(self, name: str) -> None:
        super().enable_secondary_index(name)
        if name in self._secondary_index_cache:
            del self._secondary_index_cache[name]

    def watch(self, run_id: str, cursor: str | None, callback: EventHandlerFn) -> None:
        # SQL Server has no LISTEN/NOTIFY equivalent that dagster can use without extra
        # infrastructure (Query Notifications require Service Broker), so watching polls.
        if cursor and EventLogCursor.parse(cursor).is_offset_cursor():
            check.failed("Cannot call `watch` with an offset cursor")

        if self._event_watcher is None:
            self._event_watcher = SqlPollingEventWatcher(self)

        self._event_watcher.watch_run(run_id, cursor, callback)

    def end_watch(self, run_id: str, handler: EventHandlerFn) -> None:
        if self._event_watcher:
            self._event_watcher.unwatch_run(run_id, handler)

    def dispose(self) -> None:
        if self._event_watcher:
            self._event_watcher.close()
            self._event_watcher = None

    def alembic_version(self) -> AlembicVersion:
        alembic_config = mssql_alembic_config(__file__)
        with self._connect() as conn:
            return check_alembic_revision(alembic_config, conn)
