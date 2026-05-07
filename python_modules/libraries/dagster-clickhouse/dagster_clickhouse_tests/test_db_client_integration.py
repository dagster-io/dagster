"""Integration tests against a real ClickHouse instance (Docker)."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from clickhouse_driver import Client  # ty: ignore[unresolved-import]
from dagster._core.definitions.partitions.utils import TimeWindow
from dagster._core.storage.db_io_manager import TablePartitionDimension, TableSlice
from dagster_clickhouse.db_client import ClickhouseDbClient, format_clickhouse_table_fqn

pytestmark = pytest.mark.integration


def test_ensure_schema_exists_creates_database(clickhouse_connection):
    ch_db = "dagster_int_test_db"
    client = Client(**clickhouse_connection)
    try:
        ctx = MagicMock()
        ctx.resource_config = {}
        # Drop if exists from prior run
        client.execute(f"DROP DATABASE IF EXISTS `{ch_db}`")
        ClickhouseDbClient.ensure_schema_exists(
            ctx,
            TableSlice(schema=ch_db, table="dummy"),
            client,
        )
        rows = client.execute(f"EXISTS DATABASE `{ch_db}`")
        assert rows[0][0] == 1
    finally:
        client.execute(f"DROP DATABASE IF EXISTS `{ch_db}`")
        client.disconnect()


def test_truncate_and_partition_delete_on_real_table(clickhouse_connection):
    """TRUNCATE full table; ALTER DELETE with mutations_sync for time-window partitions."""
    ctx = MagicMock()
    ctx.resource_config = {}

    ch_db = "dagster_int_test_db"
    table = "part_test"
    fqn = format_clickhouse_table_fqn(TableSlice(schema=ch_db, table=table))

    client = Client(**clickhouse_connection)
    try:
        client.execute(f"DROP DATABASE IF EXISTS `{ch_db}`")
        client.execute(f"CREATE DATABASE IF NOT EXISTS `{ch_db}`")
        client.execute(
            f"CREATE TABLE IF NOT EXISTS {fqn} (ts DateTime, v Int64) "
            "ENGINE = MergeTree() ORDER BY tuple()"
        )
        client.execute(
            f"INSERT INTO {fqn} VALUES ('2020-01-15 00:00:00', 1), ('2020-02-15 00:00:00', 2)"
        )

        slice_part = TableSlice(
            schema=ch_db,
            table=table,
            partition_dimensions=[
                TablePartitionDimension(
                    partition_expr="ts",
                    partitions=TimeWindow(datetime(2020, 1, 1), datetime(2020, 2, 1)),
                )
            ],
        )
        ClickhouseDbClient.delete_table_slice(ctx, slice_part, client)

        # Remaining row should be February only
        cnt = client.execute(f"SELECT count() FROM {fqn}")[0][0]
        assert cnt == 1

        slice_full = TableSlice(schema=ch_db, table=table)
        ClickhouseDbClient.delete_table_slice(ctx, slice_full, client)
        cnt2 = client.execute(f"SELECT count() FROM {fqn}")[0][0]
        assert cnt2 == 0
    finally:
        client.execute(f"DROP DATABASE IF EXISTS `{ch_db}`")
        client.disconnect()


def test_delete_table_unknown_table_is_ignored(clickhouse_connection):
    """TRUNCATE IF EXISTS on a missing table in an existing database should not raise."""
    ctx = MagicMock()
    ctx.resource_config = {}
    ch_db = "dagster_missing_tbl_test"
    client = Client(**clickhouse_connection)
    try:
        client.execute(f"CREATE DATABASE IF NOT EXISTS `{ch_db}`")
        ClickhouseDbClient.delete_table_slice(
            ctx,
            TableSlice(schema=ch_db, table="missing_tbl"),
            client,
        )
    finally:
        client.execute(f"DROP DATABASE IF EXISTS `{ch_db}`")
        client.disconnect()
