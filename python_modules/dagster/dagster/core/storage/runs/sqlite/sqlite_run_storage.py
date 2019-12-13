import os
from contextlib import contextmanager

from sqlalchemy.pool import NullPool

from dagster import check
from dagster.core.definitions.environment_configs import SystemNamedDict
from dagster.core.serdes import ConfigurableClass, ConfigurableClassData
from dagster.core.types import String
from dagster.core.types.config import Field
from dagster.seven import urlparse
from dagster.utils import mkdir_p

from ...sql import create_engine, get_alembic_config, stamp_alembic_rev
from ..schema import RunStorageSqlMetadata
from ..sql_run_storage import SqlRunStorage


class SqliteRunStorage(SqlRunStorage, ConfigurableClass):
    def __init__(self, conn_string, inst_data=None):
        check.str_param(conn_string, 'conn_string')
        self._conn_string = conn_string
        self._inst_data = check.opt_inst_param(inst_data, 'inst_data', ConfigurableClassData)

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return SystemNamedDict('SqliteRunStorageConfig', {'base_dir': Field(String)})

    @staticmethod
    def from_config_value(inst_data, config_value, **kwargs):
        return SqliteRunStorage.from_local(inst_data=inst_data, **dict(config_value, **kwargs))

    @staticmethod
    def from_local(base_dir, inst_data=None):
        check.str_param(base_dir, 'base_dir')
        mkdir_p(base_dir)
        path_components = os.path.abspath(base_dir).split(os.sep)
        conn_string = 'sqlite:///{}'.format('/'.join(path_components + ['runs.db']))
        engine = create_engine(conn_string, poolclass=NullPool)
        RunStorageSqlMetadata.create_all(engine)
        alembic_config = get_alembic_config(__file__)
        conn = engine.connect()
        try:
            stamp_alembic_rev(alembic_config, conn)
        finally:
            conn.close()

        return SqliteRunStorage(conn_string, inst_data)

    @contextmanager
    def connect(self):
        engine = create_engine(self._conn_string, poolclass=NullPool)
        conn = engine.connect()
        try:
            yield conn
        finally:
            conn.close()

    def upgrade(self):
        path_to_old_db = os.path.join(
            os.path.split(os.path.abspath(urlparse(self._conn_string).path))[0], '..', 'runs.db'
        )
        if os.path.exists(path_to_old_db):
            old_conn_string = 'sqlite:///{}'.format('/'.join(path_to_old_db.split(os.sep)))
            old_storage = SqliteRunStorage(old_conn_string)
            old_runs = old_storage.all_runs()
            for run in old_runs:
                self.add_run(run)

        os.unlink(path_to_old_db)
