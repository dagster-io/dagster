from typing import Dict

import sqlalchemy as db
from packaging.version import parse

import dagster._check as check
from dagster._core.storage.config import mysql_config
from dagster._core.storage.runs import (
    DaemonHeartbeatsTable,
    InstanceInfo,
    RunStorageSqlMetadata,
    SqlRunStorage,
)
from dagster._core.storage.runs.schema import KeyValueStoreTable
from dagster._core.storage.sql import (
    check_alembic_revision,
    create_engine,
    run_alembic_upgrade,
    stamp_alembic_rev,
)
from dagster._serdes import ConfigurableClass, ConfigurableClassData, serialize_dagster_namedtuple
from dagster._utils import utc_datetime_from_timestamp

from ..utils import (
    MYSQL_POOL_RECYCLE,
    create_mysql_connection,
    mysql_alembic_config,
    mysql_url_from_config,
    retry_mysql_connection_fn,
    retry_mysql_creation_fn,
)

MINIMUM_MYSQL_BUCKET_VERSION = "8.0.0"


class MySQLRunStorage(SqlRunStorage, ConfigurableClass):
    """MySQL-backed run storage.

    Users should not directly instantiate this class; it is instantiated by internal machinery when
    ``dagit`` and ``dagster-graphql`` load, based on the values in the ``dagster.yaml`` file in
    ``$DAGSTER_HOME``. Configuration of this class should be done by setting values in that file.


    .. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/deploying/dagster-mysql-legacy.yaml
       :caption: dagster.yaml
       :start-after: start_marker_runs
       :end-before: end_marker_runs
       :language: YAML

    Note that the fields in this config are :py:class:`~dagster.StringSource` and
    :py:class:`~dagster.IntSource` and can be configured from environment variables.
    """

    def __init__(self, mysql_url, inst_data=None):
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self.mysql_url = mysql_url

        # Default to not holding any connections open to prevent accumulating connections per DagsterInstance
        self._engine = create_engine(
            self.mysql_url,
            isolation_level="AUTOCOMMIT",
            poolclass=db.pool.NullPool,
        )

        self._index_migration_cache = {}
        table_names = retry_mysql_connection_fn(db.inspect(self._engine).get_table_names)

        # Stamp and create tables if the main table does not exist (we can't check alembic
        # revision because alembic config may be shared with other storage classes)
        if "runs" not in table_names:
            retry_mysql_creation_fn(self._init_db)
            self.migrate()
            self.optimize()

        elif "instance_info" not in table_names:
            InstanceInfo.create(self._engine)

        self._mysql_version = self.get_server_version()

        super().__init__()

    def _init_db(self):
        with self.connect() as conn:
            with conn.begin():
                RunStorageSqlMetadata.create_all(conn)
                stamp_alembic_rev(mysql_alembic_config(__file__), conn)

    def optimize_for_dagit(self, statement_timeout):
        # When running in dagit, hold 1 open connection
        # https://github.com/dagster-io/dagster/issues/3719
        self._engine = create_engine(
            self.mysql_url,
            isolation_level="AUTOCOMMIT",
            pool_size=1,
            pool_recycle=MYSQL_POOL_RECYCLE,
        )

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return mysql_config()

    def get_server_version(self):
        row = self.fetchone("select version()")
        if not row:
            return None

        return row[0]

    @staticmethod
    def from_config_value(inst_data, config_value):
        return MySQLRunStorage(inst_data=inst_data, mysql_url=mysql_url_from_config(config_value))

    @staticmethod
    def wipe_storage(mysql_url):
        engine = create_engine(mysql_url, isolation_level="AUTOCOMMIT", poolclass=db.pool.NullPool)
        try:
            RunStorageSqlMetadata.drop_all(engine)
        finally:
            engine.dispose()

    @staticmethod
    def create_clean_storage(mysql_url):
        MySQLRunStorage.wipe_storage(mysql_url)
        return MySQLRunStorage(mysql_url)

    def connect(self, run_id=None):  # pylint: disable=arguments-differ, unused-argument
        return create_mysql_connection(self._engine, __file__, "run")

    def upgrade(self):
        alembic_config = mysql_alembic_config(__file__)
        with self.connect() as conn:
            run_alembic_upgrade(alembic_config, conn)

    def has_built_index(self, migration_name):
        if migration_name not in self._index_migration_cache:
            self._index_migration_cache[migration_name] = super(
                MySQLRunStorage, self
            ).has_built_index(migration_name)
        return self._index_migration_cache[migration_name]

    def mark_index_built(self, migration_name):
        super(MySQLRunStorage, self).mark_index_built(migration_name)
        if migration_name in self._index_migration_cache:
            del self._index_migration_cache[migration_name]

    @property
    def supports_bucket_queries(self):
        if not super().supports_bucket_queries:
            return False

        if not self._mysql_version:
            return False

        return parse(self._mysql_version) >= parse(MINIMUM_MYSQL_BUCKET_VERSION)

    def add_daemon_heartbeat(self, daemon_heartbeat):
        with self.connect() as conn:
            conn.execute(
                db.dialects.mysql.insert(DaemonHeartbeatsTable)
                .values(
                    timestamp=utc_datetime_from_timestamp(daemon_heartbeat.timestamp),
                    daemon_type=daemon_heartbeat.daemon_type,
                    daemon_id=daemon_heartbeat.daemon_id,
                    body=serialize_dagster_namedtuple(daemon_heartbeat),
                )
                .on_duplicate_key_update(
                    timestamp=utc_datetime_from_timestamp(daemon_heartbeat.timestamp),
                    daemon_id=daemon_heartbeat.daemon_id,
                    body=serialize_dagster_namedtuple(daemon_heartbeat),
                )
            )

    def kvs_set(self, pairs: Dict[str, str]) -> None:
        check.dict_param(pairs, "pairs", key_type=str, value_type=str)
        db_values = [{"key": k, "value": v} for k, v in pairs.items()]

        with self.connect() as conn:
            insert_stmt = db.dialects.mysql.insert(KeyValueStoreTable).values(db_values)
            conn.execute(
                insert_stmt.on_duplicate_key_update(
                    value=insert_stmt.inserted.value,
                )
            )

    def alembic_version(self):
        alembic_config = mysql_alembic_config(__file__)
        with self.connect() as conn:
            return check_alembic_revision(alembic_config, conn)
