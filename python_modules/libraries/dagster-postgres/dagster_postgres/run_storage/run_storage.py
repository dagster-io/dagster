import zlib
from collections.abc import Mapping
from typing import ContextManager, Optional  # noqa: UP035

import dagster._check as check
import sqlalchemy as db
import sqlalchemy.dialects as db_dialects
import sqlalchemy.pool as db_pool
from dagster._config.config_schema import UserConfigSchema
from dagster._core.storage.config import PostgresStorageConfig, pg_config
from dagster._core.storage.runs import (
    DaemonHeartbeatsTable,
    InstanceInfo,
    RunStorageSqlMetadata,
    SqlRunStorage,
)
from dagster._core.storage.runs.schema import KeyValueStoreTable, SnapshotsTable
from dagster._core.storage.runs.sql_run_storage import SnapshotType
from dagster._core.storage.sql import (
    AlembicVersion,
    check_alembic_revision,
    create_engine,
    run_alembic_upgrade,
    stamp_alembic_rev,
)
from dagster._daemon.types import DaemonHeartbeat
from dagster._serdes import ConfigurableClass, ConfigurableClassData, serialize_value
from dagster._time import datetime_from_timestamp
from sqlalchemy import event
from sqlalchemy.engine import Connection

from dagster_postgres.utils import (
    create_pg_connection,
    pg_alembic_config,
    pg_url_from_config,
    retry_pg_connection_fn,
    retry_pg_creation_fn,
    set_pg_statement_timeout,
)


class PostgresRunStorage(SqlRunStorage, ConfigurableClass):
    """Postgres-backed run storage.

    Users should not directly instantiate this class; it is instantiated by internal machinery when
    ``dagster-webserver`` and ``dagster-graphql`` load, based on the values in the ``dagster.yaml`` file in
    ``$DAGSTER_HOME``. Configuration of this class should be done by setting values in that file.

    To use Postgres for all of the components of your instance storage, you can add the following
    block to your ``dagster.yaml``:

    .. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/deploying/dagster-pg.yaml
       :caption: dagster.yaml
       :lines: 1-8
       :language: YAML

    If you are configuring the different storage components separately and are specifically
    configuring your run storage to use Postgres, you can add a block such as the following
    to your ``dagster.yaml``:

    .. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/deploying/dagster-pg-legacy.yaml
       :caption: dagster.yaml
       :lines: 1-10
       :language: YAML

    Note that the fields in this config are :py:class:`~dagster.StringSource` and
    :py:class:`~dagster.IntSource` and can be configured from environment variables.
    """

    def __init__(
        self,
        postgres_url: str,
        should_autocreate_tables: bool = True,
        inst_data: Optional[ConfigurableClassData] = None,
    ):
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self.postgres_url = postgres_url
        self.should_autocreate_tables = check.bool_param(
            should_autocreate_tables, "should_autocreate_tables"
        )

        # Default to not holding any connections open to prevent accumulating connections per DagsterInstance
        self._engine = create_engine(
            self.postgres_url,
            isolation_level="AUTOCOMMIT",
            poolclass=db_pool.NullPool,
        )

        self._index_migration_cache = {}

        # Stamp and create tables if the main table does not exist (we can't check alembic
        # revision because alembic config may be shared with other storage classes)
        if self.should_autocreate_tables:
            table_names = retry_pg_connection_fn(lambda: db.inspect(self._engine).get_table_names())
            if "runs" not in table_names:
                retry_pg_creation_fn(self._init_db)
                self.migrate()
                self.optimize()
            elif "instance_info" not in table_names:
                InstanceInfo.create(self._engine)

        super().__init__()

    def _init_db(self) -> None:
        with self.connect() as conn:
            with conn.begin():
                RunStorageSqlMetadata.create_all(conn)
                # This revision may be shared by any other dagster storage classes using the same DB
                stamp_alembic_rev(pg_alembic_config(__file__), conn)

    def optimize_for_webserver(self, statement_timeout: int, pool_recycle: int) -> None:
        # When running in dagster-webserver, hold an open connection and set statement_timeout
        kwargs = {
            "isolation_level": "AUTOCOMMIT",
            "pool_size": 1,
            "pool_recycle": pool_recycle,
        }
        existing_options = self._engine.url.query.get("options")
        if existing_options:
            kwargs["connect_args"] = {"options": existing_options}
        self._engine = create_engine(self.postgres_url, **kwargs)
        event.listen(
            self._engine,
            "connect",
            lambda connection, _: set_pg_statement_timeout(connection, statement_timeout),
        )

    @property
    def inst_data(self) -> Optional[ConfigurableClassData]:
        return self._inst_data

    @classmethod
    def config_type(cls) -> UserConfigSchema:
        return pg_config()

    @classmethod
    def from_config_value(
        cls, inst_data: Optional[ConfigurableClassData], config_value: PostgresStorageConfig
    ):
        return PostgresRunStorage(
            inst_data=inst_data,
            postgres_url=pg_url_from_config(config_value),
            should_autocreate_tables=config_value.get("should_autocreate_tables", True),
        )

    @staticmethod
    def create_clean_storage(
        postgres_url: str, should_autocreate_tables: bool = True
    ) -> "PostgresRunStorage":
        engine = create_engine(
            postgres_url, isolation_level="AUTOCOMMIT", poolclass=db_pool.NullPool
        )
        try:
            RunStorageSqlMetadata.drop_all(engine)
        finally:
            engine.dispose()
        return PostgresRunStorage(postgres_url, should_autocreate_tables)

    def connect(self) -> ContextManager[Connection]:
        return create_pg_connection(self._engine)

    def upgrade(self) -> None:
        with self.connect() as conn:
            run_alembic_upgrade(pg_alembic_config(__file__), conn)

    def has_built_index(self, migration_name: str) -> bool:
        if migration_name not in self._index_migration_cache:
            self._index_migration_cache[migration_name] = super().has_built_index(migration_name)
        return self._index_migration_cache[migration_name]

    def mark_index_built(self, migration_name: str) -> None:
        super().mark_index_built(migration_name)
        if migration_name in self._index_migration_cache:
            del self._index_migration_cache[migration_name]

    def add_daemon_heartbeat(self, daemon_heartbeat: DaemonHeartbeat) -> None:
        with self.connect() as conn:
            # insert or update if already present, using postgres specific on_conflict
            conn.execute(
                db_dialects.postgresql.insert(DaemonHeartbeatsTable)
                .values(
                    timestamp=datetime_from_timestamp(daemon_heartbeat.timestamp),
                    daemon_type=daemon_heartbeat.daemon_type,
                    daemon_id=daemon_heartbeat.daemon_id,
                    body=serialize_value(daemon_heartbeat),
                )
                .on_conflict_do_update(
                    index_elements=[DaemonHeartbeatsTable.c.daemon_type],
                    set_={
                        "timestamp": datetime_from_timestamp(daemon_heartbeat.timestamp),
                        "daemon_id": daemon_heartbeat.daemon_id,
                        "body": serialize_value(daemon_heartbeat),
                    },
                )
                .returning(
                    # required because sqlalchemy might by default return the declared primary key,
                    # which might not exist
                    DaemonHeartbeatsTable.c.daemon_type,
                )
            )

    def set_cursor_values(self, pairs: Mapping[str, str]) -> None:
        check.mapping_param(pairs, "pairs", key_type=str, value_type=str)

        # pg specific on_conflict_do_update
        insert_stmt = db_dialects.postgresql.insert(KeyValueStoreTable).values(
            [{"key": k, "value": v} for k, v in pairs.items()]
        )
        upsert_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[
                KeyValueStoreTable.c.key,
            ],
            set_={"value": insert_stmt.excluded.value},
        ).returning(
            # required because sqlalchemy might by default return the declared primary key,
            # which might not exist
            KeyValueStoreTable.c.key
        )

        with self.connect() as conn:
            conn.execute(upsert_stmt)

    def _add_snapshot(self, snapshot_id: str, snapshot_obj, snapshot_type: SnapshotType) -> str:
        with self.connect() as conn:
            snapshot_insert = (
                db_dialects.postgresql.insert(SnapshotsTable)
                .values(
                    snapshot_id=snapshot_id,
                    snapshot_body=zlib.compress(serialize_value(snapshot_obj).encode("utf-8")),
                    snapshot_type=snapshot_type.value,
                )
                .on_conflict_do_nothing()
            )
            conn.execute(snapshot_insert)
            return snapshot_id

    def alembic_version(self) -> AlembicVersion:
        alembic_config = pg_alembic_config(__file__)
        with self.connect() as conn:
            return check_alembic_revision(alembic_config, conn)
