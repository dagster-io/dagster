from dagster.core.definitions.environment_configs import SystemNamedDict
from dagster.core.serdes import ConfigurableClass
from dagster.core.storage.runs import RunStorageSQLMetadata, SQLRunStorage, create_engine
from dagster.core.types import Field, String


class PostgresRunStorage(SQLRunStorage, ConfigurableClass):
    def __init__(self, postgres_url, inst_data=None):
        self.engine = create_engine(postgres_url)
        RunStorageSQLMetadata.create_all(self.engine)
        super(PostgresRunStorage, self).__init__(inst_data=inst_data)

    @classmethod
    def config_type(cls):
        return SystemNamedDict('PostgresRunStorageConfig', {'postgres_url': Field(String)})

    @staticmethod
    def from_config_value(config_value, **kwargs):
        return PostgresRunStorage(**dict(config_value, **kwargs))

    @staticmethod
    def create_clean_storage(postgres_url):
        engine = create_engine(postgres_url)
        RunStorageSQLMetadata.drop_all(engine)
        return PostgresRunStorage(postgres_url)

    def connect(self):
        return self.engine.connect()
