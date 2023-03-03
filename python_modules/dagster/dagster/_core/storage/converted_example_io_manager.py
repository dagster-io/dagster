from dagster._core.storage.db_io_manager import DbClient, DbTypeHandler, TableSlice
from dagster import io_manager, OutputContext, InputContext, IOManagerDefinition, IOManager, asset, materialize
from contextlib import contextmanager
from typing import Union, Optional, Mapping, Sequence, Type, Dict, Any, cast, TypeVar, Generic, List
from dagster._core.definitions.metadata import RawMetadataValue

from dagster._config.structured_config import ConfigurableIOManager, ConfigurableResource, ConfigurableIOManagerFactory
from abc import ABC, abstractmethod
from pydantic import validator, Field, BaseModel

T = TypeVar("T")

class DbClientResource(ConfigurableResource):
    database: str = Field(...)
    db_schema: str = Field(...) # schema is a reserved keyword in pydantic :(

    @staticmethod
    @abstractmethod
    def delete_table_slice(context: OutputContext, table_slice: TableSlice, connection) -> None:
        ...

    @staticmethod
    @abstractmethod
    def get_select_statement(table_slice: TableSlice) -> str:
        ...

    @staticmethod
    @abstractmethod
    def ensure_schema_exists(context: OutputContext, table_slice: TableSlice, connection) -> None:
        ...

    @staticmethod
    @contextmanager
    def connect(context: Union[OutputContext, InputContext], table_slice: TableSlice):
        ...

class DbTypeHandlerResource(ConfigurableResource):
    baz: str
    @abstractmethod
    def handle_output(
        self, context: OutputContext, table_slice: TableSlice, obj, connection
    ) -> Optional[Mapping[str, RawMetadataValue]]:
        """Stores the given object at the given table in the given schema."""

    @abstractmethod
    def load_input(self, context: InputContext, table_slice: TableSlice, connection) -> Any:
        """Loads the contents of the given table in the given schema."""

    @property
    @abstractmethod
    def supported_types(self) -> Sequence[Type[object]]:
        pass


class DbIOManager(ConfigurableIOManager):
    db_client: DbClientResource
    type_handlers: List[DbTypeHandlerResource]
    # default_load_type: Optional[Type] = None

    @validator("type_handlers")
    def validate_type_handlers(cls, v):
        print("VALIDATING TYPE HANDLERS")
        handlers_by_type: Dict[Optional[Type], DbTypeHandler] = {}
        for type_handler in v:
            for handled_type in type_handler.supported_types:
                if handled_type in handlers_by_type:
                    raise Exception(f"duplicate handler!! {type_handler}")
                handlers_by_type[handled_type] = type_handler

    @property # TODO - figure out a way to compute this once
    def handlers_by_type(self):
        print("GETTING TYPE HANDLERS BY TYPE")
        handlers_by_type: Dict[Optional[Type], DbTypeHandler] = {}
        for type_handler in self.type_handlers:
            for handled_type in type_handler.supported_types:
                handlers_by_type[handled_type] = type_handler

        return handlers_by_type

    @property # TODO - compute only once
    def _default_load_type(self):
        print("GETTING DEFAULT LOAD TYPE")
        # if self.default_load_type:
        #     return self._default_load_type
        if (len(self.type_handlers) == 1
            and len(self.type_handlers[0].supported_types) == 1
        ):
            return type_handlers[0].supported_types[0]
        return None

    def handle_output(self, context: OutputContext, obj: object) -> None:
        print("DB IO MANAGER HANDLE OUTPUT")
        table_slice = self._get_table_slice(context, context)

        if obj is not None:
            obj_type = type(obj)
            self._check_supported_type(obj_type)

            with self.db_client.connect(context, table_slice) as conn:
                self.db_client.ensure_schema_exists(context, table_slice, conn)
                self.db_client.delete_table_slice(context, table_slice, conn)

                handler_metadata = (
                    self.handlers_by_type[obj_type].handle_output(context, table_slice, obj, conn)
                    or {}
                )
        else:
            # if obj is None, assume that I/O was handled in the op body
            handler_metadata = {}

        context.add_output_metadata(
            {**handler_metadata, "Query": self.db_client.get_select_statement(table_slice)}
        )

    def load_input(self, context: InputContext) -> object:
        print("DB IO MANAGER LOAD INPUT")
        obj_type = context.dagster_type.typing_type
        if obj_type is Any and self._default_load_type is not None:
            load_type = self._default_load_type
        else:
            load_type = obj_type

        self._check_supported_type(load_type)

        table_slice = self._get_table_slice(context, cast(OutputContext, context.upstream_output))

        with self.db_client.connect(context, table_slice) as conn:
            return self.handlers_by_type[load_type].load_input(context, table_slice, conn)

    def _get_table_slice(
        self, context: Union[OutputContext, InputContext], output_context: OutputContext
    ) -> TableSlice:
        print("GET TABLE SLICE")
        asset_key_path = context.asset_key.path
        table = asset_key_path[-1]
        return TableSlice(
            table=table,
            schema=self.db_client.db_schema or "public",
            database=self.db_client.database
        )

    def _check_supported_type(self, obj_type):
        print("CHECK SUPPORTED TYPES")
        if obj_type not in self.handlers_by_type:
            raise Exception("not supported")


class ExampleDbClient(DbClientResource):
    foo: str = Field(...)

    @staticmethod
    def delete_table_slice(context: OutputContext, table_slice: TableSlice, connection) -> None:
        print("DELETING")

    @staticmethod
    def get_select_statement(table_slice: TableSlice) -> str:
        print("SELECT STATEMENT")
        return f"SELECT * from {table_slice.database}.{table_slice.schema}.{table_slice.table}"

    @staticmethod
    def ensure_schema_exists(context: OutputContext, table_slice: TableSlice, connection) -> None:
        print("SCHEMA EXISTS")

    @staticmethod
    @contextmanager
    def connect(context: Union[OutputContext, InputContext], table_slice: TableSlice):
        print("CONNECTING")
        yield 1

class ExampleTypeHandler(DbTypeHandlerResource):
    bar: str

    def handle_output(
        self, context: OutputContext, table_slice: TableSlice, obj: int, connection
    ) -> Optional[Mapping[str, RawMetadataValue]]:
        """Stores the given object at the given table in the given schema."""
        print("EXAMPLE TYPE HANDLER HANDLE OUTPUT")
        print(self.bar)
        print(self.baz)

    def load_input(self, context: InputContext, table_slice: TableSlice, connection) -> int:
        """Loads the contents of the given table in the given schema."""
        print("EXAMPLE TYPE HANDLER LOAD INPUT")
        return 1

    @property
    def supported_types(self) -> Sequence[Type[object]]:
        print("SUPPORTED TYPES")
        return [int]


@asset
def upstream() -> int:
    return 2

@asset
def downstream(upstream) -> int:
    return upstream

# resources = {
#     "io_manager": DbIOManager(
#         db_client=ExampleDbClient(
#             database="my_database",
#             db_schema="my_schema",
#             foo="bar"
#         ),
#         type_handlers=[ExampleTypeHandler(baz="world", bar="hi")]
#     )
# }

# materialize(
#     [upstream, downstream],
#     resources=resources
# )



#######

class BaseResource(ConfigurableResource):
    base_config: str

class ChildResource(BaseResource):
    child_config: str

class AnotherChildResource(BaseResource):
    another_child_config: str

class MyIOManager(ConfigurableIOManager):
    my_resource: BaseResource
    io_manager_config: str
    other_children: List[BaseResource]

    def handle_output(self, context, obj):
        pass

    def load_input(self, context):
        return 1


resources = {
    "io_manager": MyIOManager(
        my_resource=ChildResource(
            base_config="base",
            child_config="child",
        ),
        io_manager_config="io_mgr",
        other_children=[AnotherChildResource(base_config="another_child_base", another_child_config="another_child")]
    )
}

materialize(
    [upstream, downstream],
    resources=resources
)