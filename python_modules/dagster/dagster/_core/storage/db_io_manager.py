from abc import ABC, abstractmethod
from typing import (
    Dict,
    Generic,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
    cast,
)

import dagster._check as check
from dagster._core.definitions.metadata import RawMetadataValue
from dagster._core.definitions.time_window_partitions import TimeWindow
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.execution.context.input import InputContext
from dagster._core.execution.context.output import OutputContext
from dagster._core.storage.io_manager import IOManager

T = TypeVar("T")


class TablePartition(NamedTuple):
    time_window: TimeWindow
    partition_expr: str


class TableSlice(NamedTuple):
    table: str
    schema: str
    database: Optional[str] = None
    columns: Optional[Sequence[str]] = None
    partition: Optional[TablePartition] = None


class DbTypeHandler(ABC, Generic[T]):
    @abstractmethod
    def handle_output(
        self, context: OutputContext, table_slice: TableSlice, obj: T
    ) -> Optional[Mapping[str, RawMetadataValue]]:
        """Stores the given object at the given table in the given schema."""

    @abstractmethod
    def load_input(self, context: InputContext, table_slice: TableSlice) -> T:
        """Loads the contents of the given table in the given schema."""

    @property
    @abstractmethod
    def supported_types(self) -> Sequence[Type]:
        pass


class DbClient:
    @staticmethod
    @abstractmethod
    def delete_table_slice(context: OutputContext, table_slice: TableSlice) -> None:
        ...

    @staticmethod
    @abstractmethod
    def get_select_statement(table_slice: TableSlice) -> str:
        ...


class DbIOManager(IOManager):
    def __init__(
        self,
        *,
        type_handlers: Sequence[DbTypeHandler],
        db_client: DbClient,
        database: str,
        schema: Optional[str] = None,
        io_manager_name: Optional[str] = None,
    ):
        self._handlers_by_type: Dict[Optional[Type], DbTypeHandler] = {}
        self._io_manager_name = io_manager_name or self.__class__.__name__
        for type_handler in type_handlers:
            for handled_type in type_handler.supported_types:
                check.invariant(
                    handled_type not in self._handlers_by_type,
                    (
                        f"{self._io_manager_name} provided with two handlers for the same type. "
                        f"Type: '{handled_type}'. Handler classes: '{type(type_handler)}' and "
                        f"'{type(self._handlers_by_type.get(handled_type))}'."
                    ),
                )

                self._handlers_by_type[handled_type] = type_handler
        self._db_client = db_client
        self._database = database
        self._schema = schema

    def handle_output(self, context: OutputContext, obj: object) -> None:
        table_slice = self._get_table_slice(context, context)

        if obj is not None:
            obj_type = type(obj)
            check.invariant(
                obj_type in self._handlers_by_type,
                (
                    f"{self._io_manager_name} does not have a handler for type '{obj_type}'. Has"
                    " handlers "
                    "for types"
                    f" '{', '.join([str(handler_type) for handler_type in self._handlers_by_type.keys()])}'"
                ),
            )

            self._db_client.delete_table_slice(context, table_slice)

            handler_metadata = (
                self._handlers_by_type[obj_type].handle_output(context, table_slice, obj) or {}
            )
        else:
            check.invariant(
                context.dagster_type.is_nothing,
                (
                    "Unexpected 'None' output value. If a 'None' value is intentional, set the"
                    " output type to None."
                ),
            )
            # if obj is None, assume that I/O was handled in the op body
            handler_metadata = {}

        context.add_output_metadata(
            {**handler_metadata, "Query": self._db_client.get_select_statement(table_slice)}
        )

    def load_input(self, context: InputContext) -> object:
        obj_type = context.dagster_type.typing_type
        check.invariant(
            obj_type in self._handlers_by_type,
            (
                f"{self._io_manager_name} does not have a handler for type '{obj_type}'. Has"
                " handlers "
                "for types"
                f" '{', '.join([str(handler_type) for handler_type in self._handlers_by_type.keys()])}'"
            ),
        )
        return self._handlers_by_type[obj_type].load_input(
            context, self._get_table_slice(context, cast(OutputContext, context.upstream_output))
        )

    def _get_table_slice(
        self, context: Union[OutputContext, InputContext], output_context: OutputContext
    ) -> TableSlice:
        output_context_metadata = output_context.metadata or {}

        schema: str
        table: str
        time_window: Optional[TimeWindow]
        if context.has_asset_key:
            asset_key_path = context.asset_key.path
            table = asset_key_path[-1]
            if len(asset_key_path) > 1 and self._schema:
                raise DagsterInvalidDefinitionError(
                    f"Asset {asset_key_path} specifies a schema with "
                    f"its key prefixes {asset_key_path[:-1]}, but schema  "
                    f"{self._schema} was also provided via run config. "
                    "Schema can only be specified one way."
                )
            elif len(asset_key_path) > 1:
                schema = asset_key_path[-2]
            elif self._schema:
                schema = self._schema
            else:
                schema = "public"
            time_window = (
                context.asset_partitions_time_window if context.has_asset_partitions else None
            )
        else:
            table = output_context.name
            if output_context_metadata.get("schema") and self._schema:
                raise DagsterInvalidDefinitionError(
                    f"Schema {output_context_metadata.get('schema')} "
                    "specified via output metadata, but conflicting schema "
                    f"{self._schema} was provided via run_config. "
                    "Schema can only be specified one way."
                )
            elif output_context_metadata.get("schema"):
                schema = cast(str, output_context_metadata["schema"])
            elif self._schema:
                schema = self._schema
            else:
                schema = "public"
            time_window = None

        if time_window is not None:
            partition_expr = cast(str, output_context_metadata.get("partition_expr"))
            if partition_expr is None:
                raise ValueError(
                    f"Asset '{context.asset_key}' has partitions, but no 'partition_expr' metadata "
                    "value, so we don't know what column to filter it on."
                )
            partition = TablePartition(
                time_window=time_window,
                partition_expr=partition_expr,
            )
        else:
            partition = None

        return TableSlice(
            table=table,
            schema=schema,
            database=self._database,
            partition=partition,
            columns=(context.metadata or {}).get("columns"),  # type: ignore  # (mypy bug)
        )
