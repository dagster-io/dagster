from dagster._core.storage.db_io_manager import DbClient, DbIOManager, DbTypeHandler, TableSlice
from dagster import io_manager, OutputContext, InputContext, IOManagerDefinition, IOManager, asset, materialize
from contextlib import contextmanager
from typing import Union, Optional, Mapping, Sequence, Type, Dict, Any, cast, TypeVar, Generic, List
from dagster._core.definitions.metadata import RawMetadataValue

from dagster._config.structured_config import ConfigurableIOManager, ConfigurableResource, ConfigurableIOManagerFactory
from abc import ABC, abstractmethod
from pydantic import validator, Field, BaseModel


def build_example_db_io_manager(type_handlers: Sequence[DbTypeHandler], default_load_type: Optional[Type] = None):
    class ExampleDbIOManager(ConfigurableIOManagerFactory):
        database: str
        db_schema: str
        foo: str

        def create_io_manager(self, context) -> DbIOManager:
            return DbIOManager(
                db_client=ExampleDbClient(),
                database=self.database,
                schema=self.db_schema,
                type_handlers=type_handlers,
                default_load_type=default_load_type,
                io_manager_name="ExampleDbIOManager"
            )

    return ExampleDbIOManager


class ExampleDbClient(DbClient):
    @staticmethod
    def delete_table_slice(context: OutputContext, table_slice: TableSlice, connection) -> None:
        pass

    @staticmethod
    def get_select_statement(table_slice: TableSlice) -> str:
        return f"SELECT * from {table_slice.database}.{table_slice.schema}.{table_slice.table}"

    @staticmethod
    def ensure_schema_exists(context: OutputContext, table_slice: TableSlice, connection) -> None:
        pass

    @staticmethod
    @contextmanager
    def connect(context: Union[OutputContext, InputContext], table_slice: TableSlice):
        yield 1



class ExampleTypeHandler(DbTypeHandler[int]):
    def handle_output(
        self, context: OutputContext, table_slice: TableSlice, obj: int, connection
    ) -> Optional[Mapping[str, RawMetadataValue]]:
        """Stores the given object at the given table in the given schema."""
        pass

    def load_input(self, context: InputContext, table_slice: TableSlice, connection) -> int:
        """Loads the contents of the given table in the given schema."""
        return 1

    @property
    def supported_types(self) -> Sequence[Type[object]]:
        return [int]

    @staticmethod
    def config():
        return {
            "timeout": int,
            "num_retries": int
        }
