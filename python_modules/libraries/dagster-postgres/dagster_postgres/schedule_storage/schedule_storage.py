from collections.abc import Sequence
from typing import ContextManager, Optional  # noqa: UP035

import dagster._check as check
import sqlalchemy as db
import sqlalchemy.dialects as db_dialects
import sqlalchemy.pool as db_pool
from dagster._config.config_schema import UserConfigSchema
from dagster._core.definitions.asset_key import EntityKey
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AutomationConditionEvaluationWithRunIds,
)
from dagster._core.scheduler.instigation import InstigatorState
from dagster._core.storage.config import PostgresStorageConfig, pg_config
from dagster._core.storage.schedules import ScheduleStorageSqlMetadata, SqlScheduleStorage
from dagster._core.storage.schedules.schema import (
    AssetDaemonAssetEvaluationsTable,
    InstigatorsTable,
)
from dagster._core.storage.sql import (
    AlembicVersion,
    check_alembic_revision,
    create_engine,
    run_alembic_upgrade,
    stamp_alembic_rev,
)
from dagster._serdes import ConfigurableClass, ConfigurableClassData, serialize_value
from dagster._time import get_current_datetime
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


class PostgresScheduleStorage(SqlScheduleStorage, ConfigurableClass):
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
    configuring your schedule storage to use Postgres, you can add a block such as the following
    to your ``dagster.yaml``:

    .. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/deploying/dagster-pg-legacy.yaml
       :caption: dagster.yaml
       :lines: 23-32
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
            self.postgres_url, isolation_level="AUTOCOMMIT", poolclass=db_pool.NullPool
        )

        # Stamp and create tables if the main table does not exist (we can't check alembic
        # revision because alembic config may be shared with other storage classes)
        if self.should_autocreate_tables:
            table_names = retry_pg_connection_fn(lambda: db.inspect(self._engine).get_table_names())
            missing_main_table = "schedules" not in table_names and "jobs" not in table_names
            if missing_main_table:
                retry_pg_creation_fn(self._init_db)

        super().__init__()

    def _init_db(self) -> None:
        with self.connect() as conn:
            with conn.begin():
                ScheduleStorageSqlMetadata.create_all(conn)
                stamp_alembic_rev(pg_alembic_config(__file__), conn)

        # mark all the data migrations as applied
        self.migrate()
        self.optimize()

    def optimize_for_webserver(
        self, statement_timeout: int, pool_recycle: int, max_overflow: int
    ) -> None:
        # When running in dagster-webserver, hold an open connection and set statement_timeout
        kwargs = {
            "isolation_level": "AUTOCOMMIT",
            "pool_size": 1,
            "pool_recycle": pool_recycle,
            "max_overflow": max_overflow,
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
    def from_config_value(  # pyright: ignore[reportIncompatibleMethodOverride]
        cls, inst_data: Optional[ConfigurableClassData], config_value: PostgresStorageConfig
    ) -> "PostgresScheduleStorage":
        return PostgresScheduleStorage(
            inst_data=inst_data,
            postgres_url=pg_url_from_config(config_value),
            should_autocreate_tables=config_value.get("should_autocreate_tables", True),
        )

    @staticmethod
    def create_clean_storage(
        postgres_url: str, should_autocreate_tables: bool = True
    ) -> "PostgresScheduleStorage":
        engine = create_engine(
            postgres_url, isolation_level="AUTOCOMMIT", poolclass=db_pool.NullPool
        )
        try:
            ScheduleStorageSqlMetadata.drop_all(engine)
        finally:
            engine.dispose()
        return PostgresScheduleStorage(postgres_url, should_autocreate_tables)

    def connect(self, run_id: Optional[str] = None) -> ContextManager[Connection]:
        return create_pg_connection(self._engine)

    def upgrade(self) -> None:
        alembic_config = pg_alembic_config(__file__)
        with self.connect() as conn:
            run_alembic_upgrade(alembic_config, conn)

    def _add_or_update_instigators_table(self, conn: Connection, state: InstigatorState) -> None:
        selector_id = state.selector_id
        conn.execute(
            db_dialects.postgresql.insert(InstigatorsTable)
            .values(
                selector_id=selector_id,
                repository_selector_id=state.repository_selector_id,
                status=state.status.value,
                instigator_type=state.instigator_type.value,
                instigator_body=serialize_value(state),
            )
            .on_conflict_do_update(
                index_elements=[InstigatorsTable.c.selector_id],
                set_={
                    "status": state.status.value,
                    "instigator_type": state.instigator_type.value,
                    "instigator_body": serialize_value(state),
                    "update_timestamp": get_current_datetime(),
                },
            )
        )

    def add_auto_materialize_asset_evaluations(
        self,
        evaluation_id: int,
        asset_evaluations: Sequence[AutomationConditionEvaluationWithRunIds[EntityKey]],
    ):
        if not asset_evaluations:
            return

        insert_stmt = db_dialects.postgresql.insert(AssetDaemonAssetEvaluationsTable).values(
            [
                {
                    "evaluation_id": evaluation_id,
                    "asset_key": evaluation.key.to_db_string(),
                    "asset_evaluation_body": serialize_value(evaluation),
                    "num_requested": evaluation.num_requested,
                }
                for evaluation in asset_evaluations
            ]
        )
        upsert_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[
                AssetDaemonAssetEvaluationsTable.c.evaluation_id,
                AssetDaemonAssetEvaluationsTable.c.asset_key,
            ],
            set_={
                "asset_evaluation_body": insert_stmt.excluded.asset_evaluation_body,
                "num_requested": insert_stmt.excluded.num_requested,
            },
        )

        with self.connect() as conn:
            conn.execute(upsert_stmt)

    def alembic_version(self) -> AlembicVersion:
        alembic_config = pg_alembic_config(__file__)
        with self.connect() as conn:
            return check_alembic_revision(alembic_config, conn)
