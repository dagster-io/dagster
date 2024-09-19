import base64
import os
from datetime import datetime

import pytest
from dagster import InputContext, OutputContext, TimeWindow, asset, materialize
from dagster._core.storage.db_io_manager import DbTypeHandler, TablePartitionDimension, TableSlice
from dagster_gcp.bigquery.io_manager import (
    BigQueryClient,
    _get_cleanup_statement,
    build_bigquery_io_manager,
)

from dagster_gcp_tests.bigquery_tests.conftest import (
    IS_BUILDKITE,
    SHARED_BUILDKITE_BQ_CONFIG,
    temporary_bigquery_table,
)


def test_get_select_statement():
    assert (
        BigQueryClient.get_select_statement(
            TableSlice(database="db", schema="schema1", table="table1")
        )
        == "SELECT * FROM `db.schema1.table1`"
    )


def test_get_select_statement_columns():
    assert (
        BigQueryClient.get_select_statement(
            TableSlice(
                database="db",
                schema="schema1",
                table="table1",
                columns=["apple", "banana"],
            )
        )
        == "SELECT apple, banana FROM `db.schema1.table1`"
    )


def test_get_select_statement_partitioned():
    assert (
        BigQueryClient.get_select_statement(
            TableSlice(
                database="db",
                schema="schema1",
                table="table1",
                partition_dimensions=[
                    TablePartitionDimension(
                        partitions=TimeWindow(datetime(2020, 1, 2), datetime(2020, 2, 3)),
                        partition_expr="my_timestamp_col",
                    )
                ],
                columns=["apple", "banana"],
            )
        )
        == "SELECT apple, banana FROM `db.schema1.table1` WHERE\nmy_timestamp_col >= '2020-01-02"
        " 00:00:00' AND my_timestamp_col < '2020-02-03 00:00:00'"
    )


def test_get_select_statement_static_partitioned():
    assert (
        BigQueryClient.get_select_statement(
            TableSlice(
                database="db",
                schema="schema1",
                table="table1",
                partition_dimensions=[
                    TablePartitionDimension(partition_expr="my_fruit_col", partitions=["apple"])
                ],
                columns=["apple", "banana"],
            )
        )
        == "SELECT apple, banana FROM `db.schema1.table1` WHERE\nmy_fruit_col in ('apple')"
    )


def test_get_select_statement_multiple_static_partitions():
    assert (
        BigQueryClient.get_select_statement(
            TableSlice(
                database="db",
                schema="schema1",
                table="table1",
                partition_dimensions=[
                    TablePartitionDimension(
                        partition_expr="fruit_col", partitions=["apple", "banana"]
                    )
                ],
                columns=["fruit_col", "other_col"],
            )
        )
        == "SELECT fruit_col, other_col FROM `db.schema1.table1` WHERE\nfruit_col in ('apple',"
        " 'banana')"
    )


def test_get_select_statement_multi_partitioned():
    assert (
        BigQueryClient.get_select_statement(
            TableSlice(
                database="db",
                schema="schema1",
                table="table1",
                partition_dimensions=[
                    TablePartitionDimension(partition_expr="my_fruit_col", partitions=["apple"]),
                    TablePartitionDimension(
                        partitions=TimeWindow(datetime(2020, 1, 2), datetime(2020, 2, 3)),
                        partition_expr="my_timestamp_col",
                    ),
                ],
            )
        )
        == "SELECT * FROM `db.schema1.table1` WHERE\nmy_fruit_col in ('apple')"
        " AND\nmy_timestamp_col >="
        " '2020-01-02 00:00:00' AND my_timestamp_col < '2020-02-03 00:00:00'"
    )


def test_get_cleanup_statement():
    assert (
        _get_cleanup_statement(TableSlice(database="db", schema="schema1", table="table1"))
        == "TRUNCATE TABLE `db.schema1.table1`"
    )


def test_get_cleanup_statement_partitioned():
    assert (
        _get_cleanup_statement(
            TableSlice(
                database="db",
                schema="schema1",
                table="table1",
                partition_dimensions=[
                    TablePartitionDimension(
                        partitions=TimeWindow(datetime(2020, 1, 2), datetime(2020, 2, 3)),
                        partition_expr="my_timestamp_col",
                    )
                ],
            )
        )
        == "DELETE FROM `db.schema1.table1` WHERE\nmy_timestamp_col >= '2020-01-02 00:00:00' AND"
        " my_timestamp_col < '2020-02-03 00:00:00'"
    )


def test_get_cleanup_statement_static_partitioned():
    assert (
        _get_cleanup_statement(
            TableSlice(
                database="db",
                schema="schema1",
                table="table1",
                partition_dimensions=[
                    TablePartitionDimension(partition_expr="my_fruit_col", partitions=["apple"])
                ],
            )
        )
        == "DELETE FROM `db.schema1.table1` WHERE\nmy_fruit_col in ('apple')"
    )


def test_get_cleanup_statement_multi_partitioned():
    assert (
        _get_cleanup_statement(
            TableSlice(
                database="db",
                schema="schema1",
                table="table1",
                partition_dimensions=[
                    TablePartitionDimension(partition_expr="my_fruit_col", partitions=["apple"]),
                    TablePartitionDimension(
                        partitions=TimeWindow(datetime(2020, 1, 2), datetime(2020, 2, 3)),
                        partition_expr="my_timestamp_col",
                    ),
                ],
            )
        )
        == "DELETE FROM `db.schema1.table1` WHERE\nmy_fruit_col in ('apple')"
        " AND\nmy_timestamp_col >="
        " '2020-01-02 00:00:00' AND my_timestamp_col < '2020-02-03 00:00:00'"
    )


class FakeHandler(DbTypeHandler[int]):
    def handle_output(self, context: OutputContext, table_slice: TableSlice, obj: int, connection):
        connection.query(
            f"SELECT * FROM {table_slice.database}.{table_slice.schema}.{table_slice.table}"
        ).result()

    def load_input(self, context: InputContext, table_slice: TableSlice, connection) -> int:
        return 7

    @property
    def supported_types(self):
        return [int]


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE bigquery DB")
@pytest.mark.integration
def test_authenticate_via_config():
    schema = "BIGQUERY_IO_MANAGER_SCHEMA"
    with temporary_bigquery_table(
        schema_name=schema,
        column_str="FOO string",
    ) as table_name:
        asset_info = dict()

        @asset(name=table_name, key_prefix=schema)
        def test_asset() -> int:
            asset_info["gcp_creds_file"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            assert os.getenv("GOOGLE_APPLICATION_CREDENTIALS") is not None
            return 1

        old_gcp_creds_file = os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
        assert old_gcp_creds_file is not None

        passed = False

        try:
            with open(old_gcp_creds_file, "r") as f:
                gcp_creds = f.read()

            bq_io_manager = build_bigquery_io_manager([FakeHandler()]).configured(
                {
                    **SHARED_BUILDKITE_BQ_CONFIG,
                    "gcp_credentials": base64.b64encode(str.encode(gcp_creds)).decode(),
                }
            )
            resource_defs = {"io_manager": bq_io_manager}

            assert os.getenv("GOOGLE_APPLICATION_CREDENTIALS") is None

            result = materialize(
                [test_asset],
                resources=resource_defs,
            )
            passed = result.success

            assert os.getenv("GOOGLE_APPLICATION_CREDENTIALS") is None
            assert not os.path.exists(asset_info["gcp_creds_file"])
        finally:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = old_gcp_creds_file
            assert passed
