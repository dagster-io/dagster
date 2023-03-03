from .db_io_manager import DbClient, DbTypeHandler, TableSlice
from dagster import io_manager, OutputContext, InputContext, IOManagerDefinition, IOManager
from contextlib import contextmanager
from typing import Union, Optional, Mapping, Sequence, Type, Dict, Any, cast
from dagster._core.definitions.metadata import RawMetadataValue


class DbIOManager(IOManager):
    def __init__(
        self,
        *,
        type_handlers: Sequence[DbTypeHandler],
        db_client: DbClient,
        database: str,
        schema: Optional[str] = None,
        io_manager_name: Optional[str] = None,
        default_load_type: Optional[Type] = None,
    ):
        self._handlers_by_type: Dict[Optional[Type], DbTypeHandler] = {}
        self._io_manager_name = io_manager_name or self.__class__.__name__
        for type_handler in type_handlers:
            for handled_type in type_handler.supported_types:
                self._handlers_by_type[handled_type] = type_handler
        self._db_client = db_client
        self._database = database
        self._schema = schema
        if (
            default_load_type is None
            and len(type_handlers) == 1
            and len(type_handlers[0].supported_types) == 1
        ):
            self._default_load_type = type_handlers[0].supported_types[0]
        else:
            self._default_load_type = default_load_type

    def handle_output(self, context: OutputContext, obj: object) -> None:
        table_slice = self._get_table_slice(context, context)

        if obj is not None:
            obj_type = type(obj)
            self._check_supported_type(obj_type)

            with self._db_client.connect(context, table_slice) as conn:
                self._db_client.ensure_schema_exists(context, table_slice, conn)
                self._db_client.delete_table_slice(context, table_slice, conn)

                handler_metadata = (
                    self._handlers_by_type[obj_type].handle_output(context, table_slice, obj, conn)
                    or {}
                )
        else:
            # if obj is None, assume that I/O was handled in the op body
            handler_metadata = {}

        context.add_output_metadata(
            {**handler_metadata, "Query": self._db_client.get_select_statement(table_slice)}
        )

    def load_input(self, context: InputContext) -> object:
        obj_type = context.dagster_type.typing_type
        if obj_type is Any and self._default_load_type is not None:
            load_type = self._default_load_type
        else:
            load_type = obj_type

        self._check_supported_type(load_type)

        table_slice = self._get_table_slice(context, cast(OutputContext, context.upstream_output))

        with self._db_client.connect(context, table_slice) as conn:
            return self._handlers_by_type[load_type].load_input(context, table_slice, conn)

    def _get_table_slice(
        self, context: Union[OutputContext, InputContext], output_context: OutputContext
    ) -> TableSlice:
        asset_key_path = context.asset_key.path
        table = asset_key_path[-1]
        return TableSlice(
            table=table,
            schema=self._schema or "public",
            database=self._database
        )

    def _check_supported_type(self, obj_type):
        pass

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


def build_example_db_io_manager(type_handlers: Sequence[DbTypeHandler], default_load_type: Optional[Type] = None) -> IOManagerDefinition:
    @io_manager(
        config_schema={
            "database": str,
            "schema": str,
            "foo": str
        }
    )
    def example_db_io_manager(context):
        return DbIOManager(
            type_handlers=type_handlers,
            db_client=ExampleDbClient(),
            io_manager_name="ExampleIOManager",
            database=init_context.resource_config["database"],
            schema=init_context.resource_config.get("schema"),
            default_load_type=default_load_type,
        )

    return example_db_io_manager


example_db_example_type_io_manager = build_example_db_io_manager(type_handlers=[ExampleTypeHandler()], default_load_type=int)