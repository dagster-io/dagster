from contextlib import contextmanager

from dagster import check
from dagster.core.definitions.environment_configs import SystemNamedDict
from dagster.core.serdes import ConfigurableClass, ConfigurableClassData
from dagster.core.storage.runs import RunStorageSqlMetadata, SqlRunStorage
from dagster.core.storage.sql import create_engine, get_alembic_config, run_alembic_upgrade
from dagster.core.types import String
from dagster.core.types.config import Field


class PostgresRunStorage(SqlRunStorage, ConfigurableClass):
    def __init__(self, postgres_url, inst_data=None):
        self.engine = create_engine(postgres_url)
        RunStorageSqlMetadata.create_all(self.engine)
        self._inst_data = check.opt_inst_param(inst_data, 'inst_data', ConfigurableClassData)

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return SystemNamedDict('PostgresRunStorageConfig', {'postgres_url': Field(String)})

    @staticmethod
    def from_config_value(inst_data, config_value, **kwargs):
        return PostgresRunStorage(inst_data=inst_data, **dict(config_value, **kwargs))

    @staticmethod
    def create_clean_storage(postgres_url):
        engine = create_engine(postgres_url)
        RunStorageSqlMetadata.drop_all(engine)
        return PostgresRunStorage(postgres_url)

    @contextmanager
    def connect(self, _run_id=None):  # pylint: disable=arguments-differ
        yield self.engine.connect()

    def upgrade(self):
        alembic_config = get_alembic_config(__file__)
        run_alembic_upgrade(alembic_config, self.engine)
