from contextlib import contextmanager

from packaging.version import parse
from sqlalchemy.pool import NullPool

from dagster import (
    StringSource,
    _check as check,
)
from dagster._core.storage.sql import (
    check_alembic_revision,
    create_engine,
    get_alembic_config,
    run_alembic_upgrade,
    stamp_alembic_rev,
)
from dagster._core.storage.sqlite import create_db_conn_string, get_sqlite_version
from dagster._serdes import ConfigurableClass, ConfigurableClassData
from dagster._utils import mkdir_p

from ..schema import ScheduleStorageSqlMetadata
from ..sql_schedule_storage import SqlScheduleStorage

MINIMUM_SQLITE_BATCH_VERSION = "3.25.0"


class SqliteScheduleStorage(SqlScheduleStorage, ConfigurableClass):
    """Local SQLite backed schedule storage."""

    def __init__(self, conn_string, inst_data=None):
        check.str_param(conn_string, "conn_string")
        self._conn_string = conn_string
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)

        super().__init__()

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {"base_dir": StringSource}

    @staticmethod
    def from_config_value(inst_data, config_value):
        return SqliteScheduleStorage.from_local(inst_data=inst_data, **config_value)

    @classmethod
    def from_local(cls, base_dir, inst_data=None):
        check.str_param(base_dir, "base_dir")
        mkdir_p(base_dir)
        conn_string = create_db_conn_string(base_dir, "schedules")
        engine = create_engine(conn_string, poolclass=NullPool)
        alembic_config = get_alembic_config(__file__)

        should_migrate_data = False
        with engine.connect() as connection:
            db_revision, head_revision = check_alembic_revision(alembic_config, connection)
            if not (db_revision and head_revision):
                ScheduleStorageSqlMetadata.create_all(engine)
                engine.execute("PRAGMA journal_mode=WAL;")
                stamp_alembic_rev(alembic_config, connection)
                should_migrate_data = True

        schedule_storage = cls(conn_string, inst_data)
        if should_migrate_data:
            schedule_storage.migrate()
            schedule_storage.optimize()

        return schedule_storage

    @contextmanager
    def connect(self):
        engine = create_engine(self._conn_string, poolclass=NullPool)
        conn = engine.connect()
        try:
            yield conn
        finally:
            conn.close()

    @property
    def supports_batch_queries(self):
        if not super().supports_batch_queries:
            return False

        return super().supports_batch_queries and parse(get_sqlite_version()) >= parse(
            MINIMUM_SQLITE_BATCH_VERSION
        )

    def upgrade(self):
        alembic_config = get_alembic_config(__file__)
        with self.connect() as conn:
            run_alembic_upgrade(alembic_config, conn)

    def alembic_version(self):
        alembic_config = get_alembic_config(__file__)
        with self.connect() as conn:
            return check_alembic_revision(alembic_config, conn)
