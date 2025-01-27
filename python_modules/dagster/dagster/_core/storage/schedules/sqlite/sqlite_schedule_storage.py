from collections.abc import Iterator
from contextlib import contextmanager
from typing import Optional

import sqlalchemy as db
from packaging.version import parse
from sqlalchemy.engine import Connection
from sqlalchemy.pool import NullPool

from dagster import (
    StringSource,
    _check as check,
)
from dagster._config.config_schema import UserConfigSchema
from dagster._core.storage.schedules.schema import ScheduleStorageSqlMetadata
from dagster._core.storage.schedules.sql_schedule_storage import SqlScheduleStorage
from dagster._core.storage.sql import (
    AlembicVersion,
    check_alembic_revision,
    create_engine,
    get_alembic_config,
    run_alembic_upgrade,
    safe_commit,
    stamp_alembic_rev,
)
from dagster._core.storage.sqlite import (
    LAST_KNOWN_STAMPED_SQLITE_ALEMBIC_REVISION,
    create_db_conn_string,
    get_sqlite_version,
)
from dagster._serdes import ConfigurableClass, ConfigurableClassData
from dagster._utils import mkdir_p

MINIMUM_SQLITE_BATCH_VERSION = "3.25.0"


class SqliteScheduleStorage(SqlScheduleStorage, ConfigurableClass):
    """Local SQLite backed schedule storage."""

    def __init__(self, conn_string: str, inst_data: Optional[ConfigurableClassData] = None):
        check.str_param(conn_string, "conn_string")
        self._conn_string = conn_string
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)

        super().__init__()

    @property
    def inst_data(self) -> Optional[ConfigurableClassData]:
        return self._inst_data

    @classmethod
    def config_type(cls) -> UserConfigSchema:
        return {"base_dir": StringSource}

    @classmethod
    def from_config_value(
        cls, inst_data: Optional[ConfigurableClassData], config_value
    ) -> "SqliteScheduleStorage":
        return SqliteScheduleStorage.from_local(inst_data=inst_data, **config_value)

    @classmethod
    def from_local(
        cls, base_dir: str, inst_data: Optional[ConfigurableClassData] = None
    ) -> "SqliteScheduleStorage":
        check.str_param(base_dir, "base_dir")
        mkdir_p(base_dir)
        conn_string = create_db_conn_string(base_dir, "schedules")
        engine = create_engine(conn_string, poolclass=NullPool)
        alembic_config = get_alembic_config(__file__)

        should_migrate_data = False
        with engine.connect() as connection:
            db_revision, head_revision = check_alembic_revision(alembic_config, connection)
            if not (db_revision and head_revision):
                table_names = db.inspect(engine).get_table_names()
                if "job_ticks" in table_names:
                    # The ticks table exists but the alembic version table does not. This means that the SQLite db was
                    # initialized with SQLAlchemy 2.0 before https://github.com/dagster-io/dagster/pull/25740 was merged.
                    # We should pin the alembic revision to the last known stamped revision before we unpinned SQLAlchemy 2.0
                    # This should be safe because we have guarded all known migrations since then.
                    rev_to_stamp = LAST_KNOWN_STAMPED_SQLITE_ALEMBIC_REVISION
                else:
                    should_migrate_data = True
                    rev_to_stamp = "head"
                ScheduleStorageSqlMetadata.create_all(engine)
                connection.execute(db.text("PRAGMA journal_mode=WAL;"))
                stamp_alembic_rev(alembic_config, connection, rev=rev_to_stamp)
                safe_commit(connection)

        schedule_storage = cls(conn_string, inst_data)
        if should_migrate_data:
            schedule_storage.migrate()
            schedule_storage.optimize()

        return schedule_storage

    @contextmanager
    def connect(self) -> Iterator[Connection]:
        engine = create_engine(self._conn_string, poolclass=NullPool)
        with engine.connect() as conn:
            with conn.begin():
                yield conn

    @property
    def supports_batch_queries(self) -> bool:
        if not super().supports_batch_queries:
            return False

        return super().supports_batch_queries and parse(get_sqlite_version()) >= parse(
            MINIMUM_SQLITE_BATCH_VERSION
        )

    def upgrade(self) -> None:
        alembic_config = get_alembic_config(__file__)
        with self.connect() as conn:
            run_alembic_upgrade(alembic_config, conn)

    def alembic_version(self) -> AlembicVersion:
        alembic_config = get_alembic_config(__file__)
        with self.connect() as conn:
            return check_alembic_revision(alembic_config, conn)
