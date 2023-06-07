from typing import Sequence, Type, Union

import pandas as pd
import pyarrow as pa
import pyarrow.dataset as ds
from dagster import (
    InputContext,
    MetadataValue,
    OutputContext,
    TableColumn,
    TableSchema,
)
from dagster._core.storage.db_io_manager import (
    DbTypeHandler,
    TableSlice,
)
from deltalake import DeltaTable
from deltalake.writer import write_deltalake

from .io_manager import TableConnection


class DeltalakeArrowTypeHandler(DbTypeHandler[pa.Table]):
    def handle_output(
        self,
        context: OutputContext,
        table_slice: TableSlice,
        obj: Union[ds.Scanner, pa.Table, pa.RecordBatchReader],
        connection,
    ):
        """Stores pyarrow types in Delta table."""
        # TODO handle partition overwrites

        if isinstance(obj, ds.Scanner):
            obj = obj.to_reader()

        write_deltalake(
            connection.table_uri, obj, storage_options=connection.storage_options, mode="overwrite"
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
                **extra_info,
            }
        )

    def load_input(
        self, context: InputContext, table_slice: TableSlice, connection
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


class DeltalakePandasTypeHandler(DbTypeHandler[pd.DataFrame]):
    def handle_output(
        self,
        context: OutputContext,
        table_slice: TableSlice,
        obj: pd.DataFrame,
        connection: TableConnection,
    ):
        table_uri = f"{connection.root_uri}/{table_slice.schema}/{table_slice.table}"
        write_deltalake(
            table_uri, obj, storage_options=connection.storage_options, mode="overwrite"
        )

        context.add_output_metadata(
            {
                "row_count": obj.shape[0],
                "dataframe_columns": MetadataValue.table_schema(
                    TableSchema(
                        columns=[
                            TableColumn(name=str(name), type=str(dtype))
                            for name, dtype in obj.dtypes.items()
                        ]
                    )
                ),
            }
        )

    def load_input(
        self, context: InputContext, table_slice: TableSlice, connection: TableConnection
    ) -> pd.DataFrame:
        """Loads the input as a pandas Datafrom."""
        table_uri = f"{connection.root_uri}/{table_slice.schema}/{table_slice.table}"
        table = DeltaTable(table_uri=table_uri, storage_options=connection.storage_options)
        # TODO add predicates from select statement / table slicing ...
        scanner = table.to_pyarrow_dataset().scanner(columns=table_slice.columns)
        return scanner.to_table().to_pandas()

    @property
    def supported_types(self) -> Sequence[Type[object]]:
        return [pd.DataFrame]
