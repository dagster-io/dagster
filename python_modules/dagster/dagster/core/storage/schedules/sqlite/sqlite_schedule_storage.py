import os
from contextlib import contextmanager

from sqlalchemy.pool import NullPool

from dagster import check
from dagster.core.serdes import ConfigurableClass, ConfigurableClassData
from dagster.utils import mkdir_p

from ...sql import check_alembic_revision, create_engine, get_alembic_config, stamp_alembic_rev
from ..schema import ScheduleStorageSqlMetadata
from ..sql_schedule_storage import SqlScheduleStorage


class SqliteScheduleStorage(SqlScheduleStorage, ConfigurableClass):
    def __init__(self, conn_string, inst_data=None):
        check.str_param(conn_string, 'conn_string')
        self._conn_string = conn_string
        self._inst_data = check.opt_inst_param(inst_data, 'inst_data', ConfigurableClassData)

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {'base_dir': str}

    @staticmethod
    def from_config_value(inst_data, config_value):
        return SqliteScheduleStorage.from_local(inst_data=inst_data, **config_value)

    @staticmethod
    def from_local(base_dir, inst_data=None):
        check.str_param(base_dir, 'base_dir')
        mkdir_p(base_dir)
        path_components = os.path.abspath(base_dir).split(os.sep)
        conn_string = 'sqlite:///{}'.format('/'.join(path_components + ['schedules.db']))
        engine = create_engine(conn_string, poolclass=NullPool)
        engine.execute('PRAGMA journal_mode=WAL;')
        ScheduleStorageSqlMetadata.create_all(engine)
        alembic_config = get_alembic_config(__file__)
        db_revision, head_revision = check_alembic_revision(alembic_config, engine)
        if not (db_revision and head_revision and db_revision == head_revision):
            stamp_alembic_rev(alembic_config, engine)

        return SqliteScheduleStorage(conn_string, inst_data)

    @contextmanager
    def connect(self):
        engine = create_engine(self._conn_string, poolclass=NullPool)
        conn = engine.connect()
        try:
            yield conn
        finally:
            conn.close()

    def upgrade(self):
        pass
