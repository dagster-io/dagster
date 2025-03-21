from typing import Optional

from dagster import _check as check
from dagster._config.config_schema import UserConfigSchema
from dagster._core.storage.base_storage import DagsterStorage
from dagster._core.storage.config import PostgresStorageConfig, pg_config
from dagster._core.storage.event_log import EventLogStorage
from dagster._core.storage.runs import RunStorage
from dagster._core.storage.schedules import ScheduleStorage
from dagster._serdes import ConfigurableClass, ConfigurableClassData

from dagster_postgres.event_log import PostgresEventLogStorage
from dagster_postgres.run_storage import PostgresRunStorage
from dagster_postgres.schedule_storage import PostgresScheduleStorage
from dagster_postgres.utils import pg_url_from_config


class DagsterPostgresStorage(DagsterStorage, ConfigurableClass):
    """Postgres-backed dagster storage.

    Users should not directly instantiate this class; it is instantiated by internal machinery when
    ``dagster-webserver`` and ``dagster-daemon`` load, based on the values in the ``dagster.yaml`` file in
    ``$DAGSTER_HOME``. Configuration of this class should be done by setting values in that file.

    To use Postgres for storage, you can add a block such as the following to your
    ``dagster.yaml``:

    .. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/deploying/dagster-pg.yaml
       :caption: dagster.yaml
       :lines: 1-8
       :language: YAML

    Note that the fields in this config are :py:class:`~dagster.StringSource` and
    :py:class:`~dagster.IntSource` and can be configured from environment variables.
    """

    def __init__(
        self,
        postgres_url,
        should_autocreate_tables=True,
        inst_data: Optional[ConfigurableClassData] = None,
    ):
        self.postgres_url = postgres_url
        self.should_autocreate_tables = check.bool_param(
            should_autocreate_tables, "should_autocreate_tables"
        )
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self._run_storage = PostgresRunStorage(postgres_url, should_autocreate_tables)
        self._event_log_storage = PostgresEventLogStorage(postgres_url, should_autocreate_tables)
        self._schedule_storage = PostgresScheduleStorage(postgres_url, should_autocreate_tables)
        super().__init__()

    @property
    def inst_data(self) -> Optional[ConfigurableClassData]:
        return self._inst_data

    @classmethod
    def config_type(cls) -> UserConfigSchema:
        return pg_config()

    @classmethod
    def from_config_value(  # pyright: ignore[reportIncompatibleMethodOverride]
        cls, inst_data: Optional[ConfigurableClassData], config_value: PostgresStorageConfig
    ) -> "DagsterPostgresStorage":
        return DagsterPostgresStorage(
            inst_data=inst_data,
            postgres_url=pg_url_from_config(config_value),
            should_autocreate_tables=config_value.get("should_autocreate_tables", True),
        )

    @property
    def event_log_storage(self) -> EventLogStorage:
        return self._event_log_storage

    @property
    def run_storage(self) -> RunStorage:
        return self._run_storage

    @property
    def schedule_storage(self) -> ScheduleStorage:
        return self._schedule_storage

    @property
    def event_storage_data(self) -> Optional[ConfigurableClassData]:
        return (
            ConfigurableClassData(
                "dagster_postgres",
                "PostgresEventLogStorage",
                self.inst_data.config_yaml,
            )
            if self.inst_data
            else None
        )

    @property
    def run_storage_data(self) -> Optional[ConfigurableClassData]:
        return (
            ConfigurableClassData(
                "dagster_postgres",
                "PostgresRunStorage",
                self.inst_data.config_yaml,
            )
            if self.inst_data
            else None
        )

    @property
    def schedule_storage_data(self) -> Optional[ConfigurableClassData]:
        return (
            ConfigurableClassData(
                "dagster_postgres",
                "PostgresScheduleStorage",
                self.inst_data.config_yaml,
            )
            if self.inst_data
            else None
        )
