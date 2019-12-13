from contextlib import contextmanager

from dagster import check
from dagster.core.definitions.environment_configs import SystemNamedDict
from dagster.core.serdes import ConfigurableClass, ConfigurableClassData
from dagster.core.types import String
from dagster.core.types.config import Field
from dagster.utils import mkdir_p

from ...sql import create_engine, get_alembic_config, stamp_alembic_rev
from ..schema import RunStorageSqlMetadata
from ..sql_run_storage import SqlRunStorage


class SqliteRunStorage(SqlRunStorage, ConfigurableClass):
    def __init__(self, conn_string, inst_data=None):
        check.str_param(conn_string, 'conn_string')
        self.engine = create_engine(conn_string)
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
        conn_string = 'sqlite:///{}'.format('/'.join([base_dir, 'runs.db']))
        engine = create_engine(conn_string)
        RunStorageSqlMetadata.create_all(engine)
        alembic_config = get_alembic_config(__file__)
        stamp_alembic_rev(alembic_config, engine.connect())
        return SqliteRunStorage(conn_string, inst_data)

    @contextmanager
    def connect(self):
        yield self.engine.connect()
