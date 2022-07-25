import sqlalchemy as db

import dagster._check as check
from dagster._core.storage.config import mysql_config
from dagster._core.storage.event_log import (
    AssetKeyTable,
    SqlEventLogStorage,
    SqlEventLogStorageMetadata,
    SqlPollingEventWatcher,
)
from dagster._core.storage.event_log.base import EventLogCursor
from dagster._core.storage.event_log.migration import ASSET_KEY_INDEX_COLS
from dagster._core.storage.sql import (
    check_alembic_revision,
    create_engine,
    run_alembic_upgrade,
    stamp_alembic_rev,
)
from dagster._serdes import ConfigurableClass, ConfigurableClassData

from ..utils import (
    MYSQL_POOL_RECYCLE,
    create_mysql_connection,
    mysql_alembic_config,
    mysql_url_from_config,
    retry_mysql_connection_fn,
    retry_mysql_creation_fn,
)


class MySQLEventLogStorage(SqlEventLogStorage, ConfigurableClass):
    """MySQL-backed event log storage.

    Users should not directly instantiate this class; it is instantiated by internal machinery when
    ``dagit`` and ``dagster-graphql`` load, based on the values in the ``dagster.yaml`` file in
    ``$DAGSTER_HOME``. Configuration of this class should be done by setting values in that file.

    .. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/deploying/dagster-mysql-legacy.yaml
       :caption: dagster.yaml
       :start-after: start_marker_event_log
       :end-before: end_marker_event_log
       :language: YAML

    Note that the fields in this config are :py:class:`~dagster.StringSource` and
    :py:class:`~dagster.IntSource` and can be configured from environment variables.

    """

    def __init__(self, mysql_url, inst_data=None):
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self.mysql_url = check.str_param(mysql_url, "mysql_url")
        self._disposed = False

        self._event_watcher = SqlPollingEventWatcher(self)

        # Default to not holding any connections open to prevent accumulating connections per DagsterInstance
        self._engine = create_engine(
            self.mysql_url,
            isolation_level="AUTOCOMMIT",
            poolclass=db.pool.NullPool,
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

        super().__init__()

    def _init_db(self):
        with self._connect() as conn:
            with conn.begin():
                SqlEventLogStorageMetadata.create_all(conn)
                stamp_alembic_rev(mysql_alembic_config(__file__), conn)

    def optimize_for_dagit(self, statement_timeout):
        # When running in dagit, hold an open connection
        # https://github.com/dagster-io/dagster/issues/3719
        self._engine = create_engine(
            self.mysql_url,
            isolation_level="AUTOCOMMIT",
            pool_size=1,
            pool_recycle=MYSQL_POOL_RECYCLE,
        )

    def upgrade(self):
        alembic_config = mysql_alembic_config(__file__)
        with self._connect() as conn:
            run_alembic_upgrade(alembic_config, conn)

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return mysql_config()

    @staticmethod
    def from_config_value(inst_data, config_value):
        return MySQLEventLogStorage(
            inst_data=inst_data, mysql_url=mysql_url_from_config(config_value)
        )

    @staticmethod
    def wipe_storage(mysql_url):
        engine = create_engine(mysql_url, isolation_level="AUTOCOMMIT", poolclass=db.pool.NullPool)
        try:
            SqlEventLogStorageMetadata.drop_all(engine)
        finally:
            engine.dispose()

    @staticmethod
    def create_clean_storage(conn_string):
        MySQLEventLogStorage.wipe_storage(conn_string)
        return MySQLEventLogStorage(conn_string)

    def store_asset_event(self, event):
        # last_materialization_timestamp is updated upon observation, materialization, materialization_planned
        # See SqlEventLogStorage.store_asset_event method for more details

        values = self._get_asset_entry_values(event, self.has_secondary_index(ASSET_KEY_INDEX_COLS))
        with self.index_connection() as conn:
            if values:
                conn.execute(
                    db.dialects.mysql.insert(AssetKeyTable)
                    .values(
                        asset_key=event.dagster_event.asset_key.to_string(),
                        **values,
                    )
                    .on_duplicate_key_update(
                        **values,
                    )
                )
            else:
                try:
                    conn.execute(
                        db.dialects.mysql.insert(AssetKeyTable).values(
                            asset_key=event.dagster_event.asset_key.to_string(),
                        )
                    )
                except db.exc.IntegrityError:
                    pass

    def _connect(self):
        return create_mysql_connection(self._engine, __file__, "event log")

    def run_connection(self, run_id=None):
        return self._connect()

    def index_connection(self):
        return self._connect()

    def has_secondary_index(self, name):
        if name not in self._secondary_index_cache:
            self._secondary_index_cache[name] = super(
                MySQLEventLogStorage, self
            ).has_secondary_index(name)
        return self._secondary_index_cache[name]

    def enable_secondary_index(self, name):
        super(MySQLEventLogStorage, self).enable_secondary_index(name)
        if name in self._secondary_index_cache:
            del self._secondary_index_cache[name]

    def watch(self, run_id, cursor, callback):
        if cursor and EventLogCursor.parse(cursor).is_offset_cursor():
            check.failed("Cannot call `watch` with an offset cursor")
        self._event_watcher.watch_run(run_id, cursor, callback)

    def end_watch(self, run_id, handler):
        self._event_watcher.unwatch_run(run_id, handler)

    @property
    def event_watcher(self):
        return self._event_watcher

    def __del__(self):
        self.dispose()

    def dispose(self):
        if not self._disposed:
            self._disposed = True
            self._event_watcher.close()

    def alembic_version(self):
        alembic_config = mysql_alembic_config(__file__)
        with self._connect() as conn:
            return check_alembic_revision(alembic_config, conn)
