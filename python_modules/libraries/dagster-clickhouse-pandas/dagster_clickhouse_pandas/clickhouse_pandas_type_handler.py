from collections.abc import Mapping, Sequence

import pandas as pd
from dagster import InputContext, MetadataValue, OutputContext, TableColumn, TableSchema
from dagster._core.definitions.metadata import RawMetadataValue, TableMetadataSet
from dagster._core.storage.db_io_manager import DbTypeHandler, TableSlice
from dagster_clickhouse.db_client import (
    ClickhouseDbClient,
    _quote_ident,
    format_clickhouse_table_fqn,
)
from dagster_clickhouse.io_manager import ClickhouseIOManager, build_clickhouse_io_manager


def _pandas_dtype_to_clickhouse(dtype) -> str:
    if pd.api.types.is_integer_dtype(dtype):
        return "Int64"
    if pd.api.types.is_float_dtype(dtype):
        return "Float64"
    if pd.api.types.is_bool_dtype(dtype):
        return "Bool"
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return "DateTime64(3)"
    return "String"


class ClickhousePandasTypeHandler(DbTypeHandler[pd.DataFrame]):
    """Stores and loads Pandas DataFrames in ClickHouse via ``clickhouse-driver``."""

    def handle_output(
        self, context: OutputContext, table_slice: TableSlice, obj: pd.DataFrame, connection
    ) -> Mapping[str, RawMetadataValue]:
        fqn = format_clickhouse_table_fqn(table_slice)
        if len(obj.columns) > 0:
            cols = []
            for col, dtype in obj.dtypes.items():
                ch_type = _pandas_dtype_to_clickhouse(dtype)
                has_nulls = bool(obj[col].isnull().any())
                if has_nulls:
                    ch_type = f"Nullable({ch_type})"
                cols.append(f"{_quote_ident(str(col))} {ch_type}")

            cols_sql = ", ".join(cols)
            create_sql = (
                f"CREATE TABLE IF NOT EXISTS {fqn} ({cols_sql}) "
                "ENGINE = MergeTree() ORDER BY tuple()"
            )
            connection.execute(create_sql)

        if len(obj.columns) > 0 and not obj.empty:
            cols = ", ".join(_quote_ident(str(c)) for c in obj.columns)
            connection.insert_dataframe(
                f"INSERT INTO {fqn} ({cols}) VALUES",
                obj,
                settings={"use_numpy": True},
            )

        return {
            **(
                TableMetadataSet(partition_row_count=obj.shape[0], storage_kind="clickhouse")
                if context.has_partition_key
                else TableMetadataSet(row_count=obj.shape[0], storage_kind="clickhouse")
            ),
            "dataframe_columns": MetadataValue.table_schema(
                TableSchema(
                    columns=[
                        TableColumn(name=str(name), type=str(dtype))
                        for name, dtype in obj.dtypes.items()
                    ]
                )
            ),
        }

    def load_input(
        self, context: InputContext, table_slice: TableSlice, connection
    ) -> pd.DataFrame:
        if table_slice.partition_dimensions and len(context.asset_partition_keys) == 0:
            return pd.DataFrame()
        return connection.query_dataframe(
            ClickhouseDbClient.get_select_statement(table_slice),
            settings={"use_numpy": True},
        )

    @property
    def supported_types(self):
        return [pd.DataFrame]


clickhouse_pandas_io_manager = build_clickhouse_io_manager(
    [ClickhousePandasTypeHandler()], default_load_type=pd.DataFrame
)
clickhouse_pandas_io_manager.__doc__ = """
An I/O manager that reads and writes Pandas DataFrames to ClickHouse. Unannotated inputs and outputs
default to ``pandas.DataFrame``.

Returns:
    IOManagerDefinition
"""


class ClickhousePandasIOManager(ClickhouseIOManager):
    """I/O manager for Pandas DataFrames stored in ClickHouse."""

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @staticmethod
    def type_handlers() -> Sequence[DbTypeHandler]:
        return [ClickhousePandasTypeHandler()]

    @staticmethod
    def default_load_type() -> type | None:
        return pd.DataFrame
