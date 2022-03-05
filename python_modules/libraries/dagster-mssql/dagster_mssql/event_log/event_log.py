import sqlalchemy as db

from dagster import check
from dagster.core.storage.event_log import (
    SqlEventLogStorage,
    SqlEventLogStorageMetadata,
    SqlPollingEventWatcher,
)
from dagster.core.storage.sql import stamp_alembic_rev  # pylint: disable=unused-import
from dagster.core.storage.sql import create_engine, run_alembic_upgrade
from dagster.serdes import ConfigurableClass, ConfigurableClassData
from dagster.utils.backcompat import experimental_class_warning

from ..utils import (
    MSSQL_POOL_RECYCLE,
    create_mssql_connection,
    mssql_alembic_config,
    mssql_config,
    mssql_url_from_config,
    retry_mssql_connection_fn,
    retry_mssql_creation_fn,
)

CHANNEL_NAME = "run_events"


class MSSQLEventLogStorage(SqlEventLogStorage, ConfigurableClass):
    """MSSQL-backed event log storage.

    Users should not directly instantiate this class; it is instantiated by internal machinery when
    ``dagit`` and ``dagster-graphql`` load, based on the values in the ``dagster.yaml`` file in
    ``$DAGSTER_HOME``. Configuration of this class should be done by setting values in that file.

    .. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/deploying/dagster-mssql.yaml
       :caption: dagster.yaml
       :start-after: start_marker_event_log
       :end-before: end_marker_event_log
       :language: YAML

    Note that the fields in this config are :py:class:`~dagster.StringSource` and
    :py:class:`~dagster.IntSource` and can be configured from environment variables.

    """

    def __init__(self, mssql_url, inst_data=None):
        experimental_class_warning("MSSQLEventLogStorage")
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self.mssql_url = check.str_param(mssql_url, "mssql_url")
        self._disposed = False

        self._event_watcher = SqlPollingEventWatcher(self)

        # Default to not holding any connections open to prevent accumulating connections per DagsterInstance
        self._engine = create_engine(
            self.mssql_url,
            isolation_level="AUTOCOMMIT",
            poolclass=db.pool.NullPool,
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

        super().__init__()

    def _init_db(self):
        with self._connect() as conn:
            with conn.begin():
                SqlEventLogStorageMetadata.create_all(conn)
                stamp_alembic_rev(mssql_alembic_config(__file__), conn)

    def optimize_for_dagit(self, statement_timeout):
        # When running in dagit, hold an open connection
        # https://github.com/dagster-io/dagster/issues/3719
        self._engine = create_engine(
            self.mssql_url,
            isolation_level="AUTOCOMMIT",
            pool_size=1,
            pool_recycle=MSSQL_POOL_RECYCLE,
        )

    def upgrade(self):
        alembic_config = mssql_alembic_config(__file__)
        with self._connect() as conn:
            run_alembic_upgrade(alembic_config, conn)

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return mssql_config()

    @staticmethod
    def from_config_value(inst_data, config_value):
        return MSSQLEventLogStorage(
            inst_data=inst_data, mssql_url=mssql_url_from_config(config_value)
        )

    @staticmethod
    def wipe_storage(mssql_url):
        engine = create_engine(mssql_url, isolation_level="AUTOCOMMIT", poolclass=db.pool.NullPool)
        try:
            SqlEventLogStorageMetadata.drop_all(engine)
        finally:
            engine.dispose()

    @staticmethod
    def create_clean_storage(conn_string):
        MSSQLEventLogStorage.wipe_storage(conn_string)
        return MSSQLEventLogStorage(conn_string)

    def _connect(self):
        return create_mssql_connection(self._engine, __file__, "event log")

    def run_connection(self, run_id=None):
        return self._connect()

    def index_connection(self):
        return self._connect()

    def has_secondary_index(self, name):
        if name not in self._secondary_index_cache:
            self._secondary_index_cache[name] = super(
                MSSQLEventLogStorage, self
            ).has_secondary_index(name)
        return self._secondary_index_cache[name]

    def enable_secondary_index(self, name):
        super(MSSQLEventLogStorage, self).enable_secondary_index(name)
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
        self.dispose()

    def dispose(self):
        if not self._disposed:
            self._disposed = True
            self._event_watcher.close()
