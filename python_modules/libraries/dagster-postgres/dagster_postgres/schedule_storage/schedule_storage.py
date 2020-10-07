import sqlalchemy as db

from dagster import check
from dagster.core.storage.schedules import ScheduleStorageSqlMetadata, SqlScheduleStorage
from dagster.core.storage.sql import create_engine, get_alembic_config, run_alembic_upgrade
from dagster.serdes import ConfigurableClass, ConfigurableClassData

from ..utils import create_pg_connection, pg_config, pg_url_from_config


class PostgresScheduleStorage(SqlScheduleStorage, ConfigurableClass):
    """Postgres-backed run storage.

    Users should not directly instantiate this class; it is instantiated by internal machinery when
    ``dagit`` and ``dagster-graphql`` load, based on the values in the ``dagster.yaml`` file in
    ``$DAGSTER_HOME``. Configuration of this class should be done by setting values in that file.

    To use Postgres for schedule storage, you can add a block such as the following to your
    ``dagster.yaml``:

    .. literalinclude:: ../../../../../examples/docs_snippets/docs_snippets/deploying/dagster-pg.yaml
       :caption: dagster.yaml
       :lines: 23-32
       :language: YAML

    Note that the fields in this config are :py:class:`~dagster.StringSource` and
    :py:class:`~dagster.IntSource` and can be configured from environment variables.
    """

    def __init__(self, postgres_url, inst_data=None):
        self.postgres_url = postgres_url
        self._engine = create_engine(
            self.postgres_url, isolation_level="AUTOCOMMIT", poolclass=db.pool.NullPool
        )
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)

        with self.connect() as conn:
            ScheduleStorageSqlMetadata.create_all(conn)

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return pg_config()

    @staticmethod
    def from_config_value(inst_data, config_value):
        return PostgresScheduleStorage(
            inst_data=inst_data, postgres_url=pg_url_from_config(config_value)
        )

    @staticmethod
    def create_clean_storage(postgres_url):
        engine = create_engine(
            postgres_url, isolation_level="AUTOCOMMIT", poolclass=db.pool.NullPool
        )
        try:
            ScheduleStorageSqlMetadata.drop_all(engine)
        finally:
            engine.dispose()
        return PostgresScheduleStorage(postgres_url)

    def connect(self, run_id=None):  # pylint: disable=arguments-differ, unused-argument
        return create_pg_connection(self._engine, __file__, "schedule")

    def upgrade(self):
        alembic_config = get_alembic_config(__file__)
        run_alembic_upgrade(alembic_config, self._engine)
