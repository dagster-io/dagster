import sqlalchemy as db

import dagster._check as check
from dagster.core.storage.runs import (
    DaemonHeartbeatsTable,
    InstanceInfo,
    RunStorageSqlMetadata,
    SqlRunStorage,
)
from dagster.core.storage.sql import (
    check_alembic_revision,
    create_engine,
    run_alembic_upgrade,
    stamp_alembic_rev,
)
from dagster.serdes import ConfigurableClass, ConfigurableClassData, serialize_dagster_namedtuple
from dagster.utils import utc_datetime_from_timestamp

from ..utils import (
    create_pg_connection,
    pg_alembic_config,
    pg_config,
    pg_statement_timeout,
    pg_url_from_config,
    retry_pg_connection_fn,
    retry_pg_creation_fn,
)


class PostgresRunStorage(SqlRunStorage, ConfigurableClass):
    """Postgres-backed run storage.

    Users should not directly instantiate this class; it is instantiated by internal machinery when
    ``dagit`` and ``dagster-graphql`` load, based on the values in the ``dagster.yaml`` file in
    ``$DAGSTER_HOME``. Configuration of this class should be done by setting values in that file.

    To use Postgres for run storage, you can add a block such as the following to your
    ``dagster.yaml``:

    .. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/deploying/dagster-pg.yaml
       :caption: dagster.yaml
       :lines: 1-10
       :language: YAML

    Note that the fields in this config are :py:class:`~dagster.StringSource` and
    :py:class:`~dagster.IntSource` and can be configured from environment variables.
    """

    def __init__(self, postgres_url, should_autocreate_tables=True, inst_data=None):
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self.postgres_url = postgres_url
        self.should_autocreate_tables = check.bool_param(
            should_autocreate_tables, "should_autocreate_tables"
        )

        # Default to not holding any connections open to prevent accumulating connections per DagsterInstance
        self._engine = create_engine(
            self.postgres_url,
            isolation_level="AUTOCOMMIT",
            poolclass=db.pool.NullPool,
        )

        self._index_migration_cache = {}
        table_names = retry_pg_connection_fn(lambda: db.inspect(self._engine).get_table_names())

        # Stamp and create tables if the main table does not exist (we can't check alembic
        # revision because alembic config may be shared with other storage classes)
        if self.should_autocreate_tables and "runs" not in table_names:
            retry_pg_creation_fn(self._init_db)
            self.migrate()
            self.optimize()

        elif "instance_info" not in table_names:
            InstanceInfo.create(self._engine)

        super().__init__()

    def _init_db(self):
        with self.connect() as conn:
            with conn.begin():
                RunStorageSqlMetadata.create_all(conn)
                # This revision may be shared by any other dagster storage classes using the same DB
                stamp_alembic_rev(pg_alembic_config(__file__), conn)

    def optimize_for_dagit(self, statement_timeout):
        # When running in dagit, hold 1 open connection and set statement_timeout
        self._engine = create_engine(
            self.postgres_url,
            isolation_level="AUTOCOMMIT",
            pool_size=1,
            connect_args={"options": pg_statement_timeout(statement_timeout)},
        )

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return pg_config()

    @staticmethod
    def from_config_value(inst_data, config_value):
        return PostgresRunStorage(
            inst_data=inst_data,
            postgres_url=pg_url_from_config(config_value),
            should_autocreate_tables=config_value.get("should_autocreate_tables", True),
        )

    @staticmethod
    def create_clean_storage(postgres_url, should_autocreate_tables=True):
        engine = create_engine(
            postgres_url, isolation_level="AUTOCOMMIT", poolclass=db.pool.NullPool
        )
        try:
            RunStorageSqlMetadata.drop_all(engine)
        finally:
            engine.dispose()
        return PostgresRunStorage(postgres_url, should_autocreate_tables)

    def connect(self):
        return create_pg_connection(
            self._engine,
            pg_alembic_config(__file__),
            "run",
        )

    def upgrade(self):
        with self.connect() as conn:
            run_alembic_upgrade(pg_alembic_config(__file__), conn)

    def has_built_index(self, migration_name):
        if migration_name not in self._index_migration_cache:
            self._index_migration_cache[migration_name] = super(
                PostgresRunStorage, self
            ).has_built_index(migration_name)
        return self._index_migration_cache[migration_name]

    def mark_index_built(self, migration_name):
        super(PostgresRunStorage, self).mark_index_built(migration_name)
        if migration_name in self._index_migration_cache:
            del self._index_migration_cache[migration_name]

    def add_daemon_heartbeat(self, daemon_heartbeat):
        with self.connect() as conn:

            # insert or update if already present, using postgres specific on_conflict
            conn.execute(
                db.dialects.postgresql.insert(DaemonHeartbeatsTable)
                .values(  # pylint: disable=no-value-for-parameter
                    timestamp=utc_datetime_from_timestamp(daemon_heartbeat.timestamp),
                    daemon_type=daemon_heartbeat.daemon_type,
                    daemon_id=daemon_heartbeat.daemon_id,
                    body=serialize_dagster_namedtuple(daemon_heartbeat),
                )
                .on_conflict_do_update(
                    index_elements=[DaemonHeartbeatsTable.c.daemon_type],
                    set_={
                        "timestamp": utc_datetime_from_timestamp(daemon_heartbeat.timestamp),
                        "daemon_id": daemon_heartbeat.daemon_id,
                        "body": serialize_dagster_namedtuple(daemon_heartbeat),
                    },
                )
            )

    def alembic_version(self):
        alembic_config = pg_alembic_config(__file__)
        with self.connect() as conn:
            return check_alembic_revision(alembic_config, conn)
