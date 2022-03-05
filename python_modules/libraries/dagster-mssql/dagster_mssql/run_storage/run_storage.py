import sqlalchemy as db

from dagster import check
from dagster.core.storage.runs import (
    InstanceInfo,
    RunStorageSqlMetadata,
    SqlRunStorage,
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


class MSSQLRunStorage(SqlRunStorage, ConfigurableClass):
    """MSSQL-backed run storage.

    Users should not directly instantiate this class; it is instantiated by internal machinery when
    ``dagit`` and ``dagster-graphql`` load, based on the values in the ``dagster.yaml`` file in
    ``$DAGSTER_HOME``. Configuration of this class should be done by setting values in that file.


    .. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/deploying/dagster-mssql.yaml
       :caption: dagster.yaml
       :start-after: start_marker_runs
       :end-before: end_marker_runs
       :language: YAML

    Note that the fields in this config are :py:class:`~dagster.StringSource` and
    :py:class:`~dagster.IntSource` and can be configured from environment variables.
    """

    def __init__(self, mssql_url, inst_data=None):
        experimental_class_warning("MSSQLRunStorage")
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self.mssql_url = mssql_url

        # Default to not holding any connections open to prevent accumulating connections per DagsterInstance
        self._engine = create_engine(
            self.mssql_url, isolation_level="AUTOCOMMIT", poolclass=db.pool.NullPool,
        )

        self._index_migration_cache = {}
        table_names = retry_mssql_connection_fn(db.inspect(self._engine).get_table_names)

        # Stamp and create tables if the main table does not exist (we can't check alembic
        # revision because alembic config may be shared with other storage classes)
        if "runs" not in table_names:
            retry_mssql_creation_fn(self._init_db)
            self.migrate()
            self.optimize()

        elif "instance_info" not in table_names:
            InstanceInfo.create(self._engine)

        super().__init__()

    def _init_db(self):
        with self.connect() as conn:
            with conn.begin():
                RunStorageSqlMetadata.create_all(conn)
                stamp_alembic_rev(mssql_alembic_config(__file__), conn)

    def optimize_for_dagit(self, statement_timeout):
        # When running in dagit, hold 1 open connection
        # https://github.com/dagster-io/dagster/issues/3719
        self._engine = create_engine(
            self.mssql_url, isolation_level="AUTOCOMMIT", pool_size=1, pool_recycle=MSSQL_POOL_RECYCLE
        )

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return mssql_config()

    @staticmethod
    def from_config_value(inst_data, config_value):
        return MSSQLRunStorage(inst_data=inst_data, mssql_url=mssql_url_from_config(config_value))

    @staticmethod
    def wipe_storage(mssql_url):
        engine = create_engine(mssql_url, isolation_level="AUTOCOMMIT", poolclass=db.pool.NullPool)
        try:
            RunStorageSqlMetadata.drop_all(engine)
        finally:
            engine.dispose()

    @staticmethod
    def create_clean_storage(mssql_url):
        MSSQLRunStorage.wipe_storage(mssql_url)
        return MSSQLRunStorage(mssql_url)

    def connect(self, run_id=None):  # pylint: disable=arguments-differ, unused-argument
        return create_mssql_connection(self._engine, __file__, "run")

    def upgrade(self):
        alembic_config = mssql_alembic_config(__file__)
        with self.connect() as conn:
            run_alembic_upgrade(alembic_config, conn)

    def has_built_index(self, migration_name):
        if migration_name not in self._index_migration_cache:
            self._index_migration_cache[migration_name] = super(
                MSSQLRunStorage, self
            ).has_built_index(migration_name)
        return self._index_migration_cache[migration_name]

    def mark_index_built(self, migration_name):
        super(MSSQLRunStorage, self).mark_index_built(migration_name)
        if migration_name in self._index_migration_cache:
            del self._index_migration_cache[migration_name]
