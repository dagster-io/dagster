from typing import List, Optional, Sequence, Tuple, Type, Union, cast

import pyarrow as pa
import pyarrow.dataset as ds
from dagster import (
    InputContext,
    MetadataValue,
    OutputContext,
    TableColumn,
    TableSchema,
)
from dagster._core.definitions.time_window_partitions import TimeWindow
from dagster._core.storage.db_io_manager import DbTypeHandler, TablePartitionDimension, TableSlice
from deltalake import DeltaTable
from deltalake.schema import (
    Field as DeltaField,
    PrimitiveType,
    Schema,
)
from deltalake.table import FilterLiteralType
from deltalake.writer import write_deltalake

from .io_manager import DELTA_DATE_FORMAT, DELTA_DATETIME_FORMAT, TableConnection


class DeltalakeArrowTypeHandler(DbTypeHandler[pa.Table]):
    def handle_output(
        self,
        context: OutputContext,
        table_slice: TableSlice,
        obj: Union[ds.Scanner, pa.Table, pa.RecordBatchReader],
        connection: TableConnection,
    ):
        """Stores pyarrow types in Delta table."""
        # TODO handle partition overwrites

        if isinstance(obj, ds.Scanner):
            obj = obj.to_reader()

        delta_schema = Schema.from_pyarrow(obj.schema)

        partition_filters = None
        partition_columns = None
        if table_slice.partition_dimensions is not None:
            partition_filters = partition_dimensions_to_dnf(
                partition_dimensions=table_slice.partition_dimensions, table_schema=delta_schema
            )

            # TODO make robust and move to function
            partition_columns = [dim.partition_expr for dim in table_slice.partition_dimensions]

        write_deltalake(
            connection.table_uri,
            obj,
            storage_options=connection.storage_options,
            mode="overwrite",
            partition_filters=partition_filters,
            partition_by=partition_columns,
        )

        if isinstance(obj, pa.Table):
            extra_info = {"row_count": obj.shape[0]}
        else:
            extra_info = {}

        context.add_output_metadata(
            {
                "table_columns": MetadataValue.table_schema(
                    TableSchema(
                        columns=[
                            TableColumn(name=name, type=str(dtype))
                            for name, dtype in zip(obj.schema.names, obj.schema.types)
                        ]
                    )
                ),
                "table_uri": connection.table_uri,
                **extra_info,
            }
        )

    def load_input(
        self, context: InputContext, table_slice: TableSlice, connection: TableConnection
    ) -> Union[ds.Scanner, pa.Table, pa.RecordBatchReader]:
        """Loads the input as a pyarrow Scanner, Table, or RecordBatchReader."""
        table = DeltaTable(
            table_uri=connection.table_uri, storage_options=connection.storage_options
        )
        # TODO add predicates from select statement / table slicing ...
        scanner = table.to_pyarrow_dataset().scanner(columns=table_slice.columns)
        if context.dagster_type.typing_type == ds.Scanner:
            return scanner
        if context.dagster_type.typing_type == pa.Table:
            return scanner.to_table()
        if context.dagster_type.typing_type == pa.RecordBatchReader:
            return scanner.to_reader()
        return scanner

    @property
    def supported_types(self) -> Sequence[Type[object]]:
        return [pa.Table, ds.Scanner, pa.RecordBatchReader]


def partition_dimensions_to_dnf(
    partition_dimensions: Sequence[TablePartitionDimension], table_schema: Schema
) -> Optional[List[FilterLiteralType]]:
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
                parts.append(_time_window_partition_dnf(partition_dimension, field.type.type))
            else:
                raise ValueError(f"Unsupported partition type {field.type.type}")
        else:
            raise ValueError(f"Unsupported partition type {field.type}")

    return parts


def _time_window_partition_dnf(
    table_partition: TablePartitionDimension, data_type: str
) -> Tuple[str, str, str]:
    partition = cast(TimeWindow, table_partition.partitions)
    start_dt, _ = partition
    if data_type == "timestamp":
        start_dt_str = start_dt.strftime(DELTA_DATETIME_FORMAT)
    elif data_type == "date":
        start_dt_str = start_dt.strftime(DELTA_DATE_FORMAT)
    else:
        raise ValueError(f"Unknown primitive type: {data_type}")

    return (table_partition.partition_expr, "=", start_dt_str)


def _field_from_schema(field_name: str, schema: Schema) -> Optional[DeltaField]:
    for field in schema.fields:
        if field.name == field_name:
            return field
    return None
