from abc import ABC, abstractmethod
from typing import (
    Any,
    Dict,
    Generic,
    List,
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
from dagster._check import CheckError
from dagster._core.definitions.metadata import RawMetadataValue
from dagster._core.definitions.multi_dimensional_partitions import (
    MultiPartitionKey,
    MultiPartitionsDefinition,
)
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.definitions.time_window_partitions import (
    TimeWindow,
    TimeWindowPartitionsDefinition,
)
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.execution.context.input import InputContext
from dagster._core.execution.context.output import OutputContext
from dagster._core.storage.io_manager import IOManager

T = TypeVar("T")


class TablePartitionDimension(NamedTuple):
    partition_expr: str
    partition: Union[TimeWindow, str]


class TableSlice(NamedTuple):
    table: str
    schema: str
    database: Optional[str] = None
    columns: Optional[Sequence[str]] = None
    partition_dimensions: Optional[Sequence[TablePartitionDimension]] = None


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
    def supported_types(self) -> Sequence[Type[object]]:
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

    @staticmethod
    def ensure_schema_exists(context: OutputContext, table_slice: TableSlice) -> None:
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
            self._check_supported_type(obj_type)

            self._db_client.delete_table_slice(context, table_slice)

            self._db_client.ensure_schema_exists(context, table_slice)
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
        self._check_supported_type(obj_type)

        return self._handlers_by_type[obj_type].load_input(
            context, self._get_table_slice(context, cast(OutputContext, context.upstream_output))
        )

    def _get_partition_value(
        self, partition_def: PartitionsDefinition, partition_key: str
    ) -> Union[TimeWindow, str]:
        if isinstance(partition_def, TimeWindowPartitionsDefinition):
            return partition_def.time_window_for_partition_key(partition_key)
        else:
            # partition is static
            return partition_key

    def _get_table_slice(
        self, context: Union[OutputContext, InputContext], output_context: OutputContext
    ) -> TableSlice:
        output_context_metadata = output_context.metadata or {}

        schema: str
        table: str
        partition_value: Optional[Union[TimeWindow, str]] = None
        partition_dimensions: List[TablePartitionDimension] = []
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
            if context.has_asset_partitions:
                partition_expr = output_context_metadata.get("partition_expr")
                if partition_expr is None:
                    raise ValueError(
                        f"Asset '{context.asset_key}' has partitions, but no 'partition_expr'"
                        " metadata value, so we don't know what column to filter it on. Specify"
                        " which column(s) of the database contains partitioned data as the"
                        " 'partition_expr' metadata."
                    )

                if isinstance(context.asset_partitions_def, MultiPartitionsDefinition):
                    multi_partition_key_mapping = cast(
                        MultiPartitionKey, context.asset_partition_key
                    ).keys_by_dimension
                    for part in context.asset_partitions_def.partitions_defs:
                        partition_key = multi_partition_key_mapping[part.name]
                        partition_value = self._get_partition_value(
                            part.partitions_def, partition_key
                        )

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
                                partition_expr=cast(str, partition_expr_str),
                                partition=partition_value,
                            )
                        )
                else:
                    partition_expr_str = cast(str, partition_expr)
                    partition_key = context.asset_partition_key
                    partition_value = self._get_partition_value(
                        context.asset_partitions_def, partition_key
                    )

                    partition_dimensions.append(
                        TablePartitionDimension(
                            partition_expr=partition_expr_str, partition=partition_value
                        )
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

        return TableSlice(
            table=table,
            schema=schema,
            database=self._database,
            partition_dimensions=partition_dimensions,
            columns=(context.metadata or {}).get("columns"),  # type: ignore  # (mypy bug)
        )

    def _check_supported_type(self, obj_type):
        if obj_type not in self._handlers_by_type:
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
