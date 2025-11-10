from abc import abstractmethod
from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, Any, Generic, Optional, TypeAlias, TypeVar, Union, cast

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
from dagster import InputContext, MetadataValue, OutputContext, TableColumn, TableSchema
from dagster._core.storage.db_io_manager import DbTypeHandler, TablePartitionDimension, TableSlice
from deltalake import CommitProperties, DeltaTable, WriterProperties, write_deltalake
from deltalake.schema import (
    Field as DeltaField,
    PrimitiveType,
    Schema,
)
from deltalake.table import FilterLiteralType

try:
    from pyarrow.parquet import filters_to_expression  # pyarrow >= 10.0.0
except ImportError:
    from pyarrow.parquet import _filters_to_expression as filters_to_expression

from dagster_deltalake.io_manager import DELTA_DATE_FORMAT, DELTA_DATETIME_FORMAT, TableConnection

if TYPE_CHECKING:
    from dagster._core.definitions.partitions.utils import TimeWindow

T = TypeVar("T")
ArrowTypes: TypeAlias = Union[pa.Table, pa.RecordBatchReader]


class DeltalakeBaseArrowTypeHandler(DbTypeHandler[T], Generic[T]):
    @abstractmethod
    def from_arrow(self, obj: pa.RecordBatchReader, target_type: type) -> T:
        pass

    @abstractmethod
    def to_arrow(self, obj: T) -> tuple[pa.RecordBatchReader, dict[str, Any]]:
        pass

    def handle_output(
        self,
        context: OutputContext,
        table_slice: TableSlice,
        obj: T,
        connection: TableConnection,
    ):
        """Stores pyarrow types in Delta table."""
        metadata = context.definition_metadata or {}
        resource_config = context.resource_config or {}
        reader, delta_params = self.to_arrow(obj=obj)
        save_mode = metadata.get("mode")
        main_save_mode = resource_config.get("mode")
        main_custom_metadata = resource_config.get("custom_metadata")
        overwrite_schema = resource_config.get("overwrite_schema")
        writerprops = resource_config.get("writer_properties")

        if save_mode is not None:
            context.log.debug(
                "IO manager mode overridden with the asset metadata mode, %s -> %s",
                main_save_mode,
                save_mode,
            )
            main_save_mode = save_mode

        # Handle default mode and partitioned table logic
        if main_save_mode is None:
            main_save_mode = "overwrite"  # default mode

        # For partitioned tables, determine the appropriate mode and predicate
        predicate = None
        if _has_partitions(table_slice):
            try:
                existing_table = DeltaTable(
                    connection.table_uri, storage_options=connection.storage_options
                )
                if main_save_mode == "overwrite":
                    predicate = _build_partition_predicate(
                        table_slice.partition_dimensions, existing_table.schema()
                    )
                    if predicate:
                        context.log.debug(
                            f"Table exists and is partitioned, using predicate to overwrite specific partition: {predicate}"
                        )
                    else:
                        # Fallback to append if we can't build predicate
                        main_save_mode = "append"
                        context.log.debug(
                            "Table exists and is partitioned, using append mode to preserve other partitions"
                        )
            except Exception:
                # Table doesn't exist, keep the original mode
                pass

        context.log.debug("Writing with mode: %s", main_save_mode)

        partition_columns = None

        if _has_partitions(table_slice):
            # TODO make robust and move to function
            partition_columns = [
                dim.partition_expr for dim in table_slice.partition_dimensions or []
            ]

        # legacy parameter
        overwrite_schema = metadata.get("overwrite_schema") or overwrite_schema

        # Prepare commit properties
        custom_metadata = metadata.get("custom_metadata") or main_custom_metadata
        commit_props = None
        if custom_metadata and isinstance(custom_metadata, dict):
            commit_props = CommitProperties(custom_metadata=custom_metadata)

        # Prepare write parameters
        write_params = {
            "table_or_uri": connection.table_uri,
            "data": reader,
            "storage_options": connection.storage_options,
            "mode": main_save_mode,
            "partition_by": partition_columns,
            "schema_mode": "overwrite" if overwrite_schema else None,
            "commit_properties": commit_props,
            "writer_properties": WriterProperties(**writerprops)  # type: ignore
            if writerprops is not None
            else writerprops,
            **delta_params,
        }

        # Add predicate if specified for partition-specific overwrite
        if predicate is not None:
            write_params["predicate"] = predicate

        write_deltalake(**write_params)

        # TODO make stats computation configurable on type handler
        dt = DeltaTable(connection.table_uri, storage_options=connection.storage_options)
        try:
            _table, stats = _get_partition_stats(dt=dt, table_slice=table_slice)
        except Exception as e:
            context.log.warn(f"error while computing table stats: {e}")
            stats = {}

        context.add_output_metadata(
            {
                "table_columns": MetadataValue.table_schema(
                    TableSchema(
                        columns=[
                            TableColumn(name=name, type=str(dtype))
                            for name, dtype in zip(reader.schema.names, reader.schema.types)
                        ]
                    )
                ),
                "table_uri": connection.table_uri,
                **stats,
            }
        )

    def load_input(
        self,
        context: InputContext,
        table_slice: TableSlice,
        connection: TableConnection,
    ) -> T:
        """Loads the input as a pyarrow Table or RecordBatchReader."""
        dataset = _table_reader(table_slice, connection)

        if context.dagster_type.typing_type == ds.Dataset:
            if table_slice.columns is not None:
                raise ValueError("Cannot select columns when loading as Dataset.")
            return dataset

        scanner = dataset.scanner(columns=table_slice.columns)
        return self.from_arrow(scanner.to_reader(), context.dagster_type.typing_type)


class DeltaLakePyArrowTypeHandler(DeltalakeBaseArrowTypeHandler[ArrowTypes]):
    def from_arrow(self, obj: pa.RecordBatchReader, target_type: type[ArrowTypes]) -> ArrowTypes:
        if target_type == pa.Table:
            return obj.read_all()
        return obj

    def to_arrow(self, obj: ArrowTypes) -> tuple[pa.RecordBatchReader, dict[str, Any]]:
        if isinstance(obj, pa.Table):
            return obj.to_reader(), {}
        if isinstance(obj, ds.Dataset):
            return obj.scanner().to_reader(), {}
        return obj, {}

    @property
    def supported_types(self) -> Sequence[type[object]]:
        return [pa.Table, pa.RecordBatchReader, ds.Dataset]


def partition_dimensions_to_dnf(
    partition_dimensions: Iterable[TablePartitionDimension],
    table_schema: Schema,
    str_values: bool = False,
) -> Optional[list[FilterLiteralType]]:
    parts = []
    for partition_dimension in partition_dimensions:
        field = _field_from_schema(partition_dimension.partition_expr, table_schema)
        if field is None:
            raise ValueError(
                f"Field {partition_dimension.partition_expr} is not part of table schema.",
                "Currently only column names are supported as partition expressions",
            )
        if isinstance(field.type, PrimitiveType):
            if field.type.type in ["timestamp", "date"]:
                filter_ = _time_window_partition_dnf(
                    partition_dimension, field.type.type, str_values
                )
                parts.append(filter_)
            elif field.type.type == "string":
                parts.append(_value_dnf(partition_dimension, field.type.type, str_values=True))
            else:
                raise ValueError(f"Unsupported partition type {field.type.type}")
        else:
            raise ValueError(f"Unsupported partition type {field.type}")

    return parts if len(parts) > 0 else None


def _value_dnf(table_partition: TablePartitionDimension, data_type: str, str_values: bool):
    # ", ".join(f"'{partition}'" for partition in table_partition.partitions)
    partition = cast("Sequence[str]", table_partition.partitions)
    if len(partition) > 1:
        raise ValueError(f"Array partition values are not yet supported: {data_type} / {partition}")
    if str_values:
        return (table_partition.partition_expr, "=", table_partition.partitions[0])

    return (table_partition.partition_expr, "=", table_partition.partitions)


def _time_window_partition_dnf(
    table_partition: TablePartitionDimension, data_type: str, str_values: bool
) -> FilterLiteralType:
    partition = cast("TimeWindow", table_partition.partitions)
    start_dt, _ = partition
    start_dt = start_dt.replace(tzinfo=None)
    if str_values:
        if data_type == "timestamp":
            start_dt = start_dt.strftime(DELTA_DATETIME_FORMAT)
        elif data_type == "date":
            start_dt = start_dt.strftime(DELTA_DATE_FORMAT)
        else:
            raise ValueError(f"Unknown primitive type: {data_type}")

    return (table_partition.partition_expr, "=", start_dt)


def _field_from_schema(field_name: str, schema: Schema) -> Optional[DeltaField]:
    for field in schema.fields:
        if field.name == field_name:
            return field
    return None


def _get_partition_stats(dt: DeltaTable, table_slice: Optional[TableSlice] = None):
    # Get all add actions
    actions_table = pa.Table.from_batches([dt.get_add_actions(flatten=True)])

    # If we have partition constraints, filter the actions table
    if table_slice is not None and _has_partitions(table_slice):
        partition_conditions = (
            partition_dimensions_to_dnf(
                partition_dimensions=table_slice.partition_dimensions or [],
                table_schema=dt.schema(),
            )
            if table_slice.partition_dimensions
            else None
        )
        if partition_conditions is not None:
            # Create a dataset from actions table and apply filter
            partition_expr = filters_to_expression([partition_conditions])
            dataset = ds.dataset(actions_table)
            filtered_dataset = dataset.filter(partition_expr)
            actions_table = filtered_dataset.to_table()

    actions_table = actions_table.select(["path", "size_bytes", "num_records"])

    # Create files array from the filtered actions
    files = pa.array(actions_table.column("path").to_pylist())
    files_table = pa.Table.from_arrays([files], names=["path"])
    table = files_table.join(actions_table, keys="path")

    stats = {
        "size_bytes": MetadataValue.int(pc.sum(table.column("size_bytes")).as_py()),
        "num_rows": MetadataValue.int(pc.sum(table.column("num_records")).as_py()),
    }

    return table, stats


def _has_partitions(table_slice: TableSlice) -> bool:
    """Check if table slice has non-empty partition dimensions."""
    return (
        table_slice.partition_dimensions is not None and len(table_slice.partition_dimensions) > 0
    )


def _format_predicate_value(value) -> Optional[str]:
    """Format a value for use in partition predicate."""
    # Handle single-element lists (common in static partitions)
    if isinstance(value, list) and len(value) == 1:
        value = value[0]

    # Format based on type
    if hasattr(value, "strftime"):  # datetime-like object
        return f"'{value.strftime('%Y-%m-%d')}'"  # type: ignore[attr-defined]
    elif isinstance(value, str):
        return f"'{value}'"
    else:
        return str(value)


def _build_partition_predicate(partition_dimensions, table_schema) -> Optional[str]:
    """Build partition predicate string from dimensions."""
    predicate_conditions = []
    for partition_dim in partition_dimensions:
        partition_condition = partition_dimensions_to_dnf(
            partition_dimensions=[partition_dim],
            table_schema=table_schema,
        )
        if partition_condition:
            # Extract tuple from list if needed
            condition_tuple = (
                partition_condition[0]
                if isinstance(partition_condition, list)
                else partition_condition
            )
            field_name, op, value = condition_tuple
            value_str = _format_predicate_value(value)
            predicate_conditions.append(f"{field_name} {op} {value_str}")

    return " AND ".join(predicate_conditions) if predicate_conditions else None


def _table_reader(table_slice: TableSlice, connection: TableConnection) -> ds.Dataset:
    table = DeltaTable(table_uri=connection.table_uri, storage_options=connection.storage_options)

    partition_expr = None
    if _has_partitions(table_slice):
        partition_conditions = partition_dimensions_to_dnf(
            partition_dimensions=table_slice.partition_dimensions or [],
            table_schema=table.schema(),
        )
        if partition_conditions is not None:
            partition_expr = filters_to_expression([partition_conditions])

    dataset = table.to_pyarrow_dataset()
    if partition_expr is not None:
        dataset = dataset.filter(partition_expr)

    return dataset
