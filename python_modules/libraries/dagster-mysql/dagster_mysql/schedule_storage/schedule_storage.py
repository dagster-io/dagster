from collections.abc import Sequence
from typing import ContextManager, Optional, cast  # noqa: UP035

import dagster._check as check
import sqlalchemy as db
import sqlalchemy.dialects as db_dialects
import sqlalchemy.pool as db_pool
from dagster._config.config_schema import UserConfigSchema
from dagster._core.definitions.asset_key import EntityKey
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AutomationConditionEvaluationWithRunIds,
)
from dagster._core.storage.config import MySqlStorageConfig, mysql_config
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
from sqlalchemy.engine import Connection

from dagster_mysql.utils import (
    create_mysql_connection,
    mysql_alembic_config,
    mysql_isolation_level,
    mysql_url_from_config,
    parse_mysql_version,
    retry_mysql_connection_fn,
    retry_mysql_creation_fn,
)

MINIMUM_MYSQL_BATCH_VERSION = "8.0.0"


class MySQLScheduleStorage(SqlScheduleStorage, ConfigurableClass):
    """MySQL-backed run storage.

    Users should not directly instantiate this class; it is instantiated by internal machinery when
    ``dagster-webserver`` and ``dagster-graphql`` load, based on the values in the ``dagster.yaml`` file in
    ``$DAGSTER_HOME``. Configuration of this class should be done by setting values in that file.

    .. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/deploying/dagster-mysql-legacy.yaml
       :caption: dagster.yaml
       :start-after: start_marker_schedules
       :end-before: end_marker_schedules
       :language: YAML

    Note that the fields in this config are :py:class:`~dagster.StringSource` and
    :py:class:`~dagster.IntSource` and can be configured from environment variables.
    """

    def __init__(self, mysql_url: str, inst_data: Optional[ConfigurableClassData] = None):
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self.mysql_url = mysql_url

        # Default to not holding any connections open to prevent accumulating connections per DagsterInstance
        self._engine = create_engine(
            self.mysql_url,
            isolation_level=mysql_isolation_level(),
            poolclass=db_pool.NullPool,
        )

        # Stamp and create tables if the main table does not exist (we can't check alembic
        # revision because alembic config may be shared with other storage classes)
        table_names = retry_mysql_connection_fn(db.inspect(self._engine).get_table_names)
        if "jobs" not in table_names:
            retry_mysql_creation_fn(self._init_db)

        self._mysql_version = self.get_server_version()

        super().__init__()

    def _init_db(self) -> None:
        with self.connect() as conn:
            ScheduleStorageSqlMetadata.create_all(conn)
            stamp_alembic_rev(mysql_alembic_config(__file__), conn)

        # mark all the data migrations as applied
        self.migrate()
        self.optimize()

    def optimize_for_webserver(
        self, statement_timeout: int, pool_recycle: int, max_overflow: int
    ) -> None:
        # When running in dagster-webserver, hold an open connection
        # https://github.com/dagster-io/dagster/issues/3719
        self._engine = create_engine(
            self.mysql_url,
            isolation_level=mysql_isolation_level(),
            pool_size=1,
            pool_recycle=pool_recycle,
            max_overflow=max_overflow,
        )

    @property
    def inst_data(self) -> Optional[ConfigurableClassData]:
        return self._inst_data

    @classmethod
    def config_type(cls) -> UserConfigSchema:
        return mysql_config()

    @classmethod
    def from_config_value(  # pyright: ignore[reportIncompatibleMethodOverride]
        cls, inst_data: Optional[ConfigurableClassData], config_value: MySqlStorageConfig
    ) -> "MySQLScheduleStorage":
        return MySQLScheduleStorage(
            inst_data=inst_data, mysql_url=mysql_url_from_config(config_value)
        )

    @staticmethod
    def wipe_storage(mysql_url: str) -> None:
        engine = create_engine(
            mysql_url, isolation_level=mysql_isolation_level(), poolclass=db_pool.NullPool
        )
        try:
            ScheduleStorageSqlMetadata.drop_all(engine)
        finally:
            engine.dispose()

    @staticmethod
    def create_clean_storage(mysql_url: str) -> "MySQLScheduleStorage":
        MySQLScheduleStorage.wipe_storage(mysql_url)
        return MySQLScheduleStorage(mysql_url)

    def connect(self) -> ContextManager[Connection]:
        return create_mysql_connection(self._engine, __file__, "schedule")

    @property
    def supports_batch_queries(self) -> bool:
        if not self._mysql_version:
            return False

        return parse_mysql_version(self._mysql_version) >= parse_mysql_version(
            MINIMUM_MYSQL_BATCH_VERSION
        )

    def get_server_version(self) -> Optional[str]:
        with self.connect() as conn:
            row = conn.execute(db.text("select version()")).fetchone()

        if not row:
            return None

        return cast(str, row[0])

    def upgrade(self) -> None:
        with self.connect() as conn:
            alembic_config = mysql_alembic_config(__file__)
            run_alembic_upgrade(alembic_config, conn)

    def _add_or_update_instigators_table(self, conn: Connection, state) -> None:
        selector_id = state.selector_id
        conn.execute(
            db_dialects.mysql.insert(InstigatorsTable)
            .values(
                selector_id=selector_id,
                repository_selector_id=state.repository_selector_id,
                status=state.status.value,
                instigator_type=state.instigator_type.value,
                instigator_body=serialize_value(state),
            )
            .on_duplicate_key_update(
                status=state.status.value,
                instigator_type=state.instigator_type.value,
                instigator_body=serialize_value(state),
                update_timestamp=get_current_datetime(),
            )
        )

    def add_auto_materialize_asset_evaluations(
        self,
        evaluation_id: int,
        asset_evaluations: Sequence[AutomationConditionEvaluationWithRunIds[EntityKey]],
    ) -> None:
        if not asset_evaluations:
            return

        # Define the base insert statement
        insert_stmt = db_dialects.mysql.insert(AssetDaemonAssetEvaluationsTable).values(
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

        # Define the upsert statement using the ON DUPLICATE KEY UPDATE syntax for MySQL
        upsert_stmt = insert_stmt.on_duplicate_key_update(
            asset_evaluation_body=insert_stmt.inserted.asset_evaluation_body,
            num_requested=insert_stmt.inserted.num_requested,
        )

        with self.connect() as conn:
            conn.execute(upsert_stmt)

    def alembic_version(self) -> AlembicVersion:
        alembic_config = mysql_alembic_config(__file__)
        with self.connect() as conn:
            return check_alembic_revision(alembic_config, conn)
