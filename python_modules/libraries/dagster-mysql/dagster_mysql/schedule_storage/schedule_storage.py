import sqlalchemy as db
from dagster import check
from dagster.core.storage.schedules import ScheduleStorageSqlMetadata, SqlScheduleStorage
from dagster.core.storage.sql import create_engine, run_alembic_upgrade, stamp_alembic_rev
from dagster.serdes import ConfigurableClass, ConfigurableClassData
from dagster.utils.backcompat import experimental_class_warning

from ..utils import (
    create_mysql_connection,
    mysql_alembic_config,
    mysql_config,
    mysql_url_from_config,
    retry_mysql_connection_fn,
    retry_mysql_creation_fn,
)


class MySQLScheduleStorage(SqlScheduleStorage, ConfigurableClass):
    """MySQL-backed run storage.

    Users should not directly instantiate this class; it is instantiated by internal machinery when
    ``dagit`` and ``dagster-graphql`` load, based on the values in the ``dagster.yaml`` file in
    ``$DAGSTER_HOME``. Configuration of this class should be done by setting values in that file.

    .. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/deploying/dagster-mysql.yaml
       :caption: dagster.yaml
       :start-after: start_marker_schedules
       :end-before: end_marker_schedules
       :language: YAML

    Note that the fields in this config are :py:class:`~dagster.StringSource` and
    :py:class:`~dagster.IntSource` and can be configured from environment variables.
    """

    def __init__(self, mysql_url, inst_data=None):
        experimental_class_warning("MySQLScheduleStorage")
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self.mysql_url = mysql_url

        # Default to not holding any connections open to prevent accumulating connections per DagsterInstance
        self._engine = create_engine(
            self.mysql_url, isolation_level="AUTOCOMMIT", poolclass=db.pool.NullPool
        )

        table_names = retry_mysql_connection_fn(db.inspect(self._engine).get_table_names)
        if "jobs" not in table_names:
            with self.connect() as conn:
                alembic_config = mysql_alembic_config(__file__)
                retry_mysql_creation_fn(lambda: ScheduleStorageSqlMetadata.create_all(conn))
                stamp_alembic_rev(alembic_config, conn)

        super().__init__()

    def optimize_for_dagit(self, statement_timeout):
        # When running in dagit, hold an open connection
        # https://github.com/dagster-io/dagster/issues/3719
        self._engine = create_engine(
            self.mysql_url,
            isolation_level="AUTOCOMMIT",
            pool_size=1,
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
    def create_clean_storage(mysql_url):
        engine = create_engine(mysql_url, isolation_level="AUTOCOMMIT", poolclass=db.pool.NullPool)
        try:
            ScheduleStorageSqlMetadata.drop_all(engine)
        finally:
            engine.dispose()
        return MySQLScheduleStorage(mysql_url)

    def connect(self, run_id=None):  # pylint: disable=arguments-differ, unused-argument
        return create_mysql_connection(self._engine, __file__, "schedule")

    def upgrade(self):
        alembic_config = mysql_alembic_config(__file__)
        run_alembic_upgrade(alembic_config, self._engine)
