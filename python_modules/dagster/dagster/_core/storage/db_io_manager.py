from abc import ABC, abstractmethod
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from typing import Any, Generic, NamedTuple, Optional, TypeVar, Union, cast

import dagster._check as check
from dagster._check import CheckError
from dagster._core.definitions.metadata import RawMetadataValue
from dagster._core.definitions.metadata.metadata_set import TableMetadataSet
from dagster._core.definitions.multi_dimensional_partitions import (
    MultiPartitionKey,
    MultiPartitionsDefinition,
)
from dagster._core.definitions.time_window_partitions import (
    TimeWindow,
    TimeWindowPartitionsDefinition,
)
from dagster._core.errors import DagsterInvalidMetadata, DagsterInvariantViolationError
from dagster._core.execution.context.input import InputContext
from dagster._core.execution.context.output import OutputContext
from dagster._core.storage.io_manager import IOManager

T = TypeVar("T")


class TablePartitionDimension(NamedTuple):
    partition_expr: str
    partitions: Union[TimeWindow, Sequence[str]]


class TableSlice(NamedTuple):
    table: str
    schema: str
    database: Optional[str] = None
    columns: Optional[Sequence[str]] = None
    partition_dimensions: Optional[Sequence[TablePartitionDimension]] = None


class DbTypeHandler(ABC, Generic[T]):
    @abstractmethod
    def handle_output(
        self, context: OutputContext, table_slice: TableSlice, obj: T, connection
    ) -> Optional[Mapping[str, RawMetadataValue]]:
        """Stores the given object at the given table in the given schema."""

    @abstractmethod
    def load_input(self, context: InputContext, table_slice: TableSlice, connection) -> T:
        """Loads the contents of the given table in the given schema."""

    @property
    @abstractmethod
    def supported_types(self) -> Sequence[type[object]]:
        pass


class DbClient(Generic[T]):
    @staticmethod
    @abstractmethod
    def delete_table_slice(
        context: OutputContext, table_slice: TableSlice, connection: T
    ) -> None: ...

    @staticmethod
    @abstractmethod
    def get_select_statement(table_slice: TableSlice) -> str: ...

    @staticmethod
    def get_table_name(table_slice: TableSlice) -> str:
        """Returns a string which is set as the dagster/table_name metadata value for an
        emitted asset. This value should be the fully qualified name of the table, including the
        schema and database, if applicable.
        """
        if not table_slice.database:
            return f"{table_slice.schema}.{table_slice.table}"

        return f"{table_slice.database}.{table_slice.schema}.{table_slice.table}"

    @staticmethod
    @abstractmethod
    def ensure_schema_exists(
        context: OutputContext, table_slice: TableSlice, connection: T
    ) -> None: ...

    @staticmethod
    @abstractmethod
    @contextmanager
    def connect(
        context: Union[OutputContext, InputContext], table_slice: TableSlice
    ) -> Iterator[T]: ...


class DbIOManager(IOManager):
    def __init__(
        self,
        *,
        type_handlers: Sequence[DbTypeHandler],
        db_client: DbClient,
        database: str,
        schema: Optional[str] = None,
        io_manager_name: Optional[str] = None,
        default_load_type: Optional[type] = None,
    ):
        self._handlers_by_type: dict[type[Any], DbTypeHandler] = {}
        self._io_manager_name = io_manager_name or self.__class__.__name__
        for type_handler in type_handlers:
            for handled_type in type_handler.supported_types:
                check.invariant(
                    handled_type not in self._handlers_by_type,
                    f"{self._io_manager_name} provided with two handlers for the same type. "
                    f"Type: '{handled_type}'. Handler classes: '{type(type_handler)}' and "
                    f"'{type(self._handlers_by_type.get(handled_type))}'.",
                )

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
        # If the output type is set to Nothing, handle_output will not be
        # called. We still need to raise an error when the return value
        # is None, but the typing type is not Nothing
        if obj is None:
            raise DagsterInvariantViolationError(
                "Unexpected 'None' output value. If a 'None' value is intentional, set the output"
                " type to None by adding return type annotation '-> None'.",
            )

        obj_type = type(obj)
        self._check_supported_type(obj_type)

        table_slice = self._get_table_slice(context, context)

        with self._db_client.connect(context, table_slice) as conn:
            self._db_client.ensure_schema_exists(context, table_slice, conn)
            self._db_client.delete_table_slice(context, table_slice, conn)

            handler = self._resolve_handler(obj_type)
            handler_metadata = handler.handle_output(context, table_slice, obj, conn)

        context.add_output_metadata(
            {
                **(handler_metadata or {}),
                "Query": self._db_client.get_select_statement(table_slice),
            }
        )

        # Try to attach relation identifier metadata to the output asset, but
        # don't fail if it errors because the user has already attached it.
        try:
            context.add_output_metadata(
                dict(TableMetadataSet(table_name=self._db_client.get_table_name(table_slice)))
            )
        except DagsterInvalidMetadata:
            pass

    def load_input(self, context: InputContext) -> object:
        obj_type = context.dagster_type.typing_type
        if obj_type is Any and self._default_load_type is not None:
            load_type = self._default_load_type
        else:
            load_type = obj_type

        self._check_supported_type(load_type)

        table_slice = self._get_table_slice(context, cast(OutputContext, context.upstream_output))

        with self._db_client.connect(context, table_slice) as conn:
            return self._resolve_handler(load_type).load_input(context, table_slice, conn)  # type: ignore  # (pyright bug)

    def _resolve_handler(self, obj_type: type) -> DbTypeHandler:
        return next(
            handler
            for type_, handler in self._handlers_by_type.items()
            if issubclass(obj_type, type_)
        )

    def _get_table_slice(
        self, context: Union[OutputContext, InputContext], output_context: OutputContext
    ) -> TableSlice:
        output_context_metadata = output_context.definition_metadata or {}

        schema: str
        table: str
        partition_dimensions: list[TablePartitionDimension] = []
        if context.has_asset_key:
            asset_key_path = context.asset_key.path
            table = asset_key_path[-1]
            # schema order of precedence: metadata, I/O manager 'schema' config, key_prefix
            if output_context_metadata.get("schema"):
                schema = cast(str, output_context_metadata["schema"])
            elif self._schema:
                schema = self._schema
            elif len(asset_key_path) > 1:
                schema = asset_key_path[-2]
            else:
                schema = "public"

            if context.has_asset_partitions:
                partition_expr = output_context_metadata.get("partition_expr")
                if partition_expr is None:
                    raise ValueError(
                        f"Asset '{context.asset_key}' has partitions, but no 'partition_expr'"
                        " metadata value, so we don't know what column it's partitioned on. To"
                        " specify a column, set this metadata value. E.g."
                        ' @asset(metadata={"partition_expr": "your_partition_column"}).'
                    )

                if isinstance(context.asset_partitions_def, MultiPartitionsDefinition):
                    multi_partition_key_mapping = cast(
                        MultiPartitionKey, context.asset_partition_key
                    ).keys_by_dimension
                    for part in context.asset_partitions_def.partitions_defs:
                        partition_key = multi_partition_key_mapping[part.name]
                        if isinstance(part.partitions_def, TimeWindowPartitionsDefinition):
                            partitions = part.partitions_def.time_window_for_partition_key(
                                partition_key
                            )
                        else:
                            partitions = [partition_key]

                        partition_expr_str = cast(Mapping[str, str], partition_expr).get(part.name)
                        if partition_expr is None:
                            raise ValueError(
                                f"Asset '{context.asset_key}' has partition {part.name}, but the"
                                f" 'partition_expr' metadata does not contain a {part.name} entry,"
                                " so we don't know what column to filter it on. Specify which"
                                " column of the database contains data for the"
                                f" {part.name} partition."
                            )
                        partition_dimensions.append(
                            TablePartitionDimension(
                                partition_expr=cast(str, partition_expr_str), partitions=partitions
                            )
                        )
                elif isinstance(context.asset_partitions_def, TimeWindowPartitionsDefinition):
                    partition_dimensions.append(
                        TablePartitionDimension(
                            partition_expr=cast(str, partition_expr),
                            partitions=(
                                context.asset_partitions_time_window
                                if context.asset_partition_keys
                                else []
                            ),
                        )
                    )
                else:
                    partition_dimensions.append(
                        TablePartitionDimension(
                            partition_expr=cast(str, partition_expr),
                            partitions=context.asset_partition_keys,
                        )
                    )
        else:
            table = output_context.name
            if output_context_metadata.get("schema"):
                schema = cast(str, output_context_metadata["schema"])
            elif self._schema:
                schema = self._schema
            else:
                schema = "public"

        return TableSlice(
            table=table,
            schema=schema,
            database=self._database,
            partition_dimensions=partition_dimensions,
            columns=(context.definition_metadata or {}).get("columns"),
        )

    def _check_supported_type(self, obj_type):
        if not issubclass(obj_type, tuple(self._handlers_by_type.keys())):
            msg = (
                f"{self._io_manager_name} does not have a handler for type '{obj_type}'. Has"
                " handlers for types"
                f" '{', '.join([str(handler_type) for handler_type in self._handlers_by_type.keys()])}'."
            )

            if obj_type is Any:
                type_hints = " or ".join(
                    [str(handler_type) for handler_type in self._handlers_by_type.keys()]
                )
                msg += f" Please add {type_hints} type hints to your assets and ops."
            else:
                msg += (
                    f" Please build the {self._io_manager_name} with an type handler for type"
                    f" '{obj_type}', so the {self._io_manager_name} can correctly handle the"
                    " output."
                )

            raise CheckError(msg)
