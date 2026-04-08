from collections.abc import Mapping, Sequence

import polars as pl
from dagster import InputContext, MetadataValue, OutputContext, TableColumn, TableSchema
from dagster._core.definitions.metadata import RawMetadataValue, TableMetadataSet
from dagster._core.storage.db_io_manager import DbTypeHandler, TableSlice
from dagster_clickhouse.db_client import (
    ClickhouseDbClient,
    _quote_ident,
    format_clickhouse_table_fqn,
)
from dagster_clickhouse.io_manager import ClickhouseIOManager, build_clickhouse_io_manager


def _polars_dtype_to_clickhouse(dtype: pl.DataType) -> str:
    if dtype in (
        pl.Int8,
        pl.Int16,
        pl.Int32,
        pl.Int64,
        pl.UInt8,
        pl.UInt16,
        pl.UInt32,
        pl.UInt64,
    ):
        return "Int64"
    if dtype in (pl.Float32, pl.Float64):
        return "Float64"
    if dtype == pl.Boolean:
        return "Bool"
    if dtype == pl.Date:
        return "Date"
    if dtype in (pl.Time, pl.Duration):
        return "String"
    if dtype.is_temporal():
        return "DateTime64(3)"
    return "String"


class ClickhousePolarsTypeHandler(DbTypeHandler[pl.DataFrame]):
    """Stores and loads Polars DataFrames in ClickHouse via ``clickhouse-driver``."""

    def handle_output(
        self, context: OutputContext, table_slice: TableSlice, obj: pl.DataFrame, connection
    ) -> Mapping[str, RawMetadataValue]:
        fqn = format_clickhouse_table_fqn(table_slice)
        if len(obj.columns) > 0:
            cols = []
            for name, dtype in zip(obj.columns, obj.dtypes, strict=True):
                ch_type = _polars_dtype_to_clickhouse(dtype)
                has_nulls = obj[name].null_count() > 0
                if has_nulls:
                    ch_type = f"Nullable({ch_type})"
                cols.append(f"{_quote_ident(str(name))} {ch_type}")

            cols_sql = ", ".join(cols)
            create_sql = (
                f"CREATE TABLE IF NOT EXISTS {fqn} ({cols_sql}) "
                "ENGINE = MergeTree() ORDER BY tuple()"
            )
            connection.execute(create_sql)

        if len(obj.columns) > 0 and obj.height > 0:
            cols = ", ".join(_quote_ident(str(c)) for c in obj.columns)
            data = obj.to_dicts()
            connection.execute(
                f"INSERT INTO {fqn} ({cols}) VALUES",
                data,
            )

        return {
            **(
                TableMetadataSet(partition_row_count=obj.height)
                if context.has_partition_key
                else TableMetadataSet(row_count=obj.height)
            ),
            "dataframe_columns": MetadataValue.table_schema(
                TableSchema(
                    columns=[
                        TableColumn(name=str(name), type=str(dtype))
                        for name, dtype in zip(obj.columns, obj.dtypes, strict=True)
                    ]
                )
            ),
        }

    def load_input(
        self, context: InputContext, table_slice: TableSlice, connection
    ) -> pl.DataFrame:
        if table_slice.partition_dimensions and len(context.asset_partition_keys) == 0:
            return pl.DataFrame()
        pdf = connection.query_dataframe(
            ClickhouseDbClient.get_select_statement(table_slice),
            settings={"use_numpy": True},
        )
        return pl.from_pandas(pdf)

    @property
    def supported_types(self):
        return [pl.DataFrame]


clickhouse_polars_io_manager = build_clickhouse_io_manager(
    [ClickhousePolarsTypeHandler()], default_load_type=pl.DataFrame
)
clickhouse_polars_io_manager.__doc__ = """
An I/O manager that reads and writes Polars DataFrames to ClickHouse. Unannotated inputs and outputs
default to ``polars.DataFrame``.

Returns:
    IOManagerDefinition
"""


class ClickhousePolarsIOManager(ClickhouseIOManager):
    """I/O manager for Polars DataFrames stored in ClickHouse."""

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @staticmethod
    def type_handlers() -> Sequence[DbTypeHandler]:
        return [ClickhousePolarsTypeHandler()]

    @staticmethod
    def default_load_type() -> type | None:
        return pl.DataFrame
