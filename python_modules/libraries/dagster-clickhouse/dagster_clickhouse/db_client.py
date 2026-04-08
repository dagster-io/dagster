from collections.abc import Sequence
from contextlib import contextmanager
from typing import cast

from clickhouse_driver import Client
from clickhouse_driver.errors import ErrorCodes, ServerException
from dagster import InputContext, OutputContext
from dagster._core.definitions.partitions.utils import TimeWindow
from dagster._core.storage.db_io_manager import DbClient, TablePartitionDimension, TableSlice

from dagster_clickhouse.resource import client_kwargs_from_resource_config

CLICKHOUSE_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def _quote_ident(name: str) -> str:
    return f"`{name.replace('`', '``')}`"


def _qualified_table_name(table_slice: TableSlice) -> str:
    """Fully qualified table name; ``TableSlice.schema`` is the ClickHouse database name."""
    return f"{_quote_ident(table_slice.schema)}.{_quote_ident(table_slice.table)}"


def format_clickhouse_table_fqn(table_slice: TableSlice) -> str:
    """Return the fully quoted ``database`.`table`` name (Dagster ``schema`` = ClickHouse database)."""
    return _qualified_table_name(table_slice)


class ClickhouseDbClient(DbClient[Client]):
    @staticmethod
    def get_table_name(table_slice: TableSlice) -> str:
        """ClickHouse uses ``database.table`` where Dagster's ``schema`` is the ClickHouse database."""
        return f"{table_slice.schema}.{table_slice.table}"

    @staticmethod
    @contextmanager
    def connect(context: InputContext | OutputContext, table_slice: TableSlice):
        cfg = context.resource_config or {}
        kwargs = client_kwargs_from_resource_config({k: v for k, v in cfg.items() if k != "schema"})
        client = Client(**kwargs)
        try:
            yield client
        finally:
            client.disconnect()

    @staticmethod
    def ensure_schema_exists(
        context: OutputContext, table_slice: TableSlice, connection: Client
    ) -> None:
        ch_db = _quote_ident(table_slice.schema)
        connection.execute(f"CREATE DATABASE IF NOT EXISTS {ch_db}")

    @staticmethod
    def delete_table_slice(
        context: OutputContext, table_slice: TableSlice, connection: Client
    ) -> None:
        fqn = _qualified_table_name(table_slice)
        try:
            if table_slice.partition_dimensions:
                where_clause = _partition_where_clause(table_slice.partition_dimensions)
                connection.execute(
                    f"ALTER TABLE {fqn} DELETE WHERE {where_clause} SETTINGS mutations_sync = 1"
                )
            else:
                connection.execute(f"TRUNCATE TABLE IF EXISTS {fqn}")
        except ServerException as exc:
            if exc.code == ErrorCodes.UNKNOWN_TABLE:
                return
            raise

    @staticmethod
    def get_select_statement(table_slice: TableSlice) -> str:
        col_str = (
            ", ".join(_quote_ident(c) for c in table_slice.columns) if table_slice.columns else "*"
        )
        fqn = _qualified_table_name(table_slice)
        if table_slice.partition_dimensions:
            query = f"SELECT {col_str} FROM {fqn} WHERE\n"
            return query + _partition_where_clause(table_slice.partition_dimensions)
        return f"SELECT {col_str} FROM {fqn}"


def _partition_where_clause(partition_dimensions: Sequence[TablePartitionDimension]) -> str:
    return " AND\n".join(
        (
            _time_window_where_clause(partition_dimension)
            if isinstance(partition_dimension.partitions, TimeWindow)
            else _static_where_clause(partition_dimension)
        )
        for partition_dimension in partition_dimensions
    )


def _time_window_where_clause(table_partition: TablePartitionDimension) -> str:
    partition = cast("TimeWindow", table_partition.partitions)
    start_dt, end_dt = partition
    start_dt_str = start_dt.strftime(CLICKHOUSE_DATETIME_FORMAT)
    end_dt_str = end_dt.strftime(CLICKHOUSE_DATETIME_FORMAT)
    expr = _quote_ident(table_partition.partition_expr)
    return f"{expr} >= '{start_dt_str}' AND {expr} < '{end_dt_str}'"


def _static_where_clause(table_partition: TablePartitionDimension) -> str:
    partitions = ", ".join(
        f"'{str(p).replace(chr(39), chr(39) * 2)}'" for p in table_partition.partitions
    )
    return f"{_quote_ident(table_partition.partition_expr)} IN ({partitions})"
