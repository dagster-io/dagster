import pendulum
import sqlalchemy as db
from packaging.version import parse

import dagster._check as check
from dagster._core.storage.config import mysql_config
from dagster._core.storage.schedules import ScheduleStorageSqlMetadata, SqlScheduleStorage
from dagster._core.storage.schedules.schema import InstigatorsTable
from dagster._core.storage.sql import (
    check_alembic_revision,
    create_engine,
    run_alembic_upgrade,
    stamp_alembic_rev,
)
from dagster._serdes import ConfigurableClass, ConfigurableClassData, serialize_dagster_namedtuple

from ..utils import (
    create_mysql_connection,
    mysql_alembic_config,
    mysql_url_from_config,
    retry_mysql_connection_fn,
    retry_mysql_creation_fn,
)

MINIMUM_MYSQL_BATCH_VERSION = "8.0.0"


class MySQLScheduleStorage(SqlScheduleStorage, ConfigurableClass):
    """MySQL-backed run storage.

    Users should not directly instantiate this class; it is instantiated by internal machinery when
    ``dagit`` and ``dagster-graphql`` load, based on the values in the ``dagster.yaml`` file in
    ``$DAGSTER_HOME``. Configuration of this class should be done by setting values in that file.

    .. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/deploying/dagster-mysql-legacy.yaml
       :caption: dagster.yaml
       :start-after: start_marker_schedules
       :end-before: end_marker_schedules
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

        # Stamp and create tables if the main table does not exist (we can't check alembic
        # revision because alembic config may be shared with other storage classes)
        table_names = retry_mysql_connection_fn(db.inspect(self._engine).get_table_names)
        if "jobs" not in table_names:
            retry_mysql_creation_fn(self._init_db)

        self._mysql_version = self.get_server_version()

        super().__init__()

    def _init_db(self):
        with self.connect() as conn:
            with conn.begin():
                ScheduleStorageSqlMetadata.create_all(conn)
                stamp_alembic_rev(mysql_alembic_config(__file__), conn)

        # mark all the data migrations as applied
        self.migrate()
        self.optimize()

    def optimize_for_dagit(self, statement_timeout, pool_recycle):
        # When running in dagit, hold an open connection
        # https://github.com/dagster-io/dagster/issues/3719
        self._engine = create_engine(
            self.mysql_url,
            isolation_level="AUTOCOMMIT",
            pool_size=1,
            pool_recycle=pool_recycle,
        )

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return mysql_config()

    @staticmethod
    def from_config_value(inst_data, config_value):
        return MySQLScheduleStorage(
            inst_data=inst_data, mysql_url=mysql_url_from_config(config_value)
        )

    @staticmethod
    def wipe_storage(mysql_url):
        engine = create_engine(mysql_url, isolation_level="AUTOCOMMIT", poolclass=db.pool.NullPool)
        try:
            ScheduleStorageSqlMetadata.drop_all(engine)
        finally:
            engine.dispose()

    @staticmethod
    def create_clean_storage(mysql_url):
        MySQLScheduleStorage.wipe_storage(mysql_url)
        return MySQLScheduleStorage(mysql_url)

    def connect(self, run_id=None):  # pylint: disable=arguments-differ, unused-argument
        return create_mysql_connection(self._engine, __file__, "schedule")

    @property
    def supports_batch_queries(self):
        if not self._mysql_version:
            return False

        return parse(self._mysql_version) >= parse(MINIMUM_MYSQL_BATCH_VERSION)

    def get_server_version(self):
        rows = self.execute("select version()")
        if not rows:
            return None

        return rows[0][0]

    def upgrade(self):
        alembic_config = mysql_alembic_config(__file__)
        run_alembic_upgrade(alembic_config, self._engine)

    def _add_or_update_instigators_table(self, conn, state):
        selector_id = state.selector_id
        conn.execute(
            db.dialects.mysql.insert(InstigatorsTable)
            .values(
                selector_id=selector_id,
                repository_selector_id=state.repository_selector_id,
                status=state.status.value,
                instigator_type=state.instigator_type.value,
                instigator_body=serialize_dagster_namedtuple(state),
            )
            .on_duplicate_key_update(
                status=state.status.value,
                instigator_type=state.instigator_type.value,
                instigator_body=serialize_dagster_namedtuple(state),
                update_timestamp=pendulum.now("UTC"),
            )
        )

    def alembic_version(self):
        alembic_config = mysql_alembic_config(__file__)
        with self.connect() as conn:
            return check_alembic_revision(alembic_config, conn)
