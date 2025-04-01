from typing import ContextManager, Optional, cast  # noqa: UP035

import dagster._check as check
import sqlalchemy as db
import sqlalchemy.dialects as db_dialects
import sqlalchemy.exc as db_exc
import sqlalchemy.pool as db_pool
from dagster._config.config_schema import UserConfigSchema
from dagster._core.event_api import EventHandlerFn
from dagster._core.events.log import EventLogEntry
from dagster._core.storage.config import MySqlStorageConfig, mysql_config
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
from dagster._serdes import ConfigurableClass, ConfigurableClassData
from sqlalchemy.engine import Connection

from dagster_mysql.utils import (
    create_mysql_connection,
    mysql_alembic_config,
    mysql_isolation_level,
    mysql_url_from_config,
    retry_mysql_connection_fn,
    retry_mysql_creation_fn,
)


class MySQLEventLogStorage(SqlEventLogStorage, ConfigurableClass):
    """MySQL-backed event log storage.

    Users should not directly instantiate this class; it is instantiated by internal machinery when
    ``dagster-webserver`` and ``dagster-graphql`` load, based on the values in the ``dagster.yaml`` file in
    ``$DAGSTER_HOME``. Configuration of this class should be done by setting values in that file.

    .. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/deploying/dagster-mysql-legacy.yaml
       :caption: dagster.yaml
       :start-after: start_marker_event_log
       :end-before: end_marker_event_log
       :language: YAML

    Note that the fields in this config are :py:class:`~dagster.StringSource` and
    :py:class:`~dagster.IntSource` and can be configured from environment variables.

    """

    def __init__(self, mysql_url: str, inst_data: Optional[ConfigurableClassData] = None):
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self.mysql_url = check.str_param(mysql_url, "mysql_url")
        self._event_watcher: Optional[SqlPollingEventWatcher] = None

        # Default to not holding any connections open to prevent accumulating connections per DagsterInstance
        self._engine = create_engine(
            self.mysql_url,
            isolation_level=mysql_isolation_level(),
            poolclass=db_pool.NullPool,
        )
        self._secondary_index_cache = {}

        table_names = retry_mysql_connection_fn(db.inspect(self._engine).get_table_names)

        # Stamp and create tables if the main table does not exist (we can't check alembic
        # revision because alembic config may be shared with other storage classes)
        if "event_logs" not in table_names:
            retry_mysql_creation_fn(self._init_db)
            # mark all secondary indexes to be used
            self.reindex_events()
            self.reindex_assets()

        self._mysql_version = self.get_server_version()
        super().__init__()

    def _init_db(self) -> None:
        with self._connect() as conn:
            SqlEventLogStorageMetadata.create_all(conn)
            stamp_alembic_rev(mysql_alembic_config(__file__), conn)

    def optimize_for_webserver(
        self, statement_timeout: int, pool_recycle: int, max_overflow: int
    ) -> None:
        # When running in dagster-webserver, hold an open connection
        # https://github.com/dagster-io/dagster/issues/3719
        self._engine = create_engine(
            self.mysql_url,
            isolation_level=mysql_isolation_level(),
            pool_size=1,
            pool_recycle=pool_recycle,
            max_overflow=max_overflow,
        )

    def upgrade(self) -> None:
        alembic_config = mysql_alembic_config(__file__)
        with self._connect() as conn:
            run_alembic_upgrade(alembic_config, conn)

    @property
    def inst_data(self) -> Optional[ConfigurableClassData]:
        return self._inst_data

    @classmethod
    def config_type(cls) -> UserConfigSchema:
        return mysql_config()

    @classmethod
    def from_config_value(  # pyright: ignore[reportIncompatibleMethodOverride]
        cls, inst_data: Optional[ConfigurableClassData], config_value: MySqlStorageConfig
    ) -> "MySQLEventLogStorage":
        return MySQLEventLogStorage(
            inst_data=inst_data, mysql_url=mysql_url_from_config(config_value)
        )

    @staticmethod
    def wipe_storage(mysql_url: str) -> None:
        engine = create_engine(
            mysql_url, isolation_level=mysql_isolation_level(), poolclass=db_pool.NullPool
        )
        try:
            SqlEventLogStorageMetadata.drop_all(engine)
        finally:
            engine.dispose()

    @staticmethod
    def create_clean_storage(conn_string: str) -> "MySQLEventLogStorage":
        MySQLEventLogStorage.wipe_storage(conn_string)
        return MySQLEventLogStorage(conn_string)

    def get_server_version(self) -> Optional[str]:
        with self.index_connection() as conn:
            row = conn.execute(db.text("select version()")).fetchone()

        if not row:
            return None

        return cast(str, row[0])

    def store_asset_event(self, event: EventLogEntry, event_id: int) -> None:
        # last_materialization_timestamp is updated upon observation, materialization, materialization_planned
        # See SqlEventLogStorage.store_asset_event method for more details

        values = self._get_asset_entry_values(
            event, event_id, self.has_secondary_index(ASSET_KEY_INDEX_COLS)
        )
        with self.index_connection() as conn:
            if values:
                conn.execute(
                    db_dialects.mysql.insert(AssetKeyTable)
                    .values(
                        asset_key=event.dagster_event.asset_key.to_string(),  # type: ignore  # (possible none)
                        **values,
                    )
                    .on_duplicate_key_update(
                        **values,
                    )
                )
            else:
                try:
                    conn.execute(
                        db_dialects.mysql.insert(AssetKeyTable).values(
                            asset_key=event.dagster_event.asset_key.to_string(),  # type: ignore  # (possible none)
                        )
                    )
                except db_exc.IntegrityError:
                    pass

    def _connect(self) -> ContextManager[Connection]:
        return create_mysql_connection(self._engine, __file__, "event log")

    def run_connection(self, run_id: Optional[str] = None) -> ContextManager[Connection]:
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

    def watch(self, run_id: str, cursor: Optional[str], callback: EventHandlerFn) -> None:
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
        alembic_config = mysql_alembic_config(__file__)
        with self._connect() as conn:
            return check_alembic_revision(alembic_config, conn)
