from typing import Sequence, Type, Optional

import pandas as pd
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

from dagster_deltalake.io_manager import DeltaTableIOManager, TableConnection


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


class DeltaTablePandasIOManager(DeltaTableIOManager):
    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @staticmethod
    def type_handlers() -> Sequence[DbTypeHandler]:
        return [DeltalakePandasTypeHandler()]

    @staticmethod
    def default_load_type() -> Optional[Type]:
        return pd.DataFrame
