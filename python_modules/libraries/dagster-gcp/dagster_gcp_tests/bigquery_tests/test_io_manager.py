import base64
import os
from datetime import datetime
from typing import Optional, Sequence, Type

import pytest
from dagster import EnvVar, InputContext, OutputContext, TimeWindow, asset, materialize
from dagster._core.storage.db_io_manager import DbTypeHandler, TablePartitionDimension, TableSlice
from dagster_gcp.auth.resources import GoogleAuthResource
from dagster_gcp.bigquery.io_manager import (
    BigQueryClient,
    BigQueryIOManager,
    _get_cleanup_statement,
    build_bigquery_io_manager,
)

IS_BUILDKITE = os.getenv("BUILDKITE") is not None

SHARED_BUILDKITE_BQ_CONFIG = {
    "project": os.getenv("GCP_PROJECT_ID"),
}


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
        connection.query("SELECT 1").result()

    def load_input(self, context: InputContext, table_slice: TableSlice, connection) -> int:
        return 7

    @property
    def supported_types(self):
        return [int]


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE bigquery DB")
def test_authenticate_via_config():
    @asset
    def test_asset(context) -> int:
        assert (
            context.resources.io_manager._db_client.auth_resource.service_account_info  # noqa: SLF001
            is not None
        )
        assert (
            context.resources.io_manager._db_client.auth_resource.service_account_file  # noqa: SLF001
            is None
        )
        return 1

    old_gcp_creds_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    assert old_gcp_creds_file is not None

    with open(old_gcp_creds_file, "r") as f:
        gcp_creds = f.read()

    bq_io_manager = build_bigquery_io_manager([FakeHandler()]).configured(
        {
            "project": os.getenv("GCP_PROJECT_ID"),
            "gcp_credentials": base64.b64encode(str.encode(gcp_creds)).decode(),
        }
    )
    resource_defs = {"io_manager": bq_io_manager}

    result = materialize(
        [test_asset],
        resources=resource_defs,
    )
    assert result.success


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE bigquery DB")
def test_authenticate_via_google_auth_resource():
    class FakeBigQueryIOManager(BigQueryIOManager):
        @staticmethod
        def type_handlers() -> Sequence[DbTypeHandler]:
            return [FakeHandler()]

        @staticmethod
        def default_load_type() -> Optional[Type]:
            return int

    @asset
    def test_asset(context) -> int:
        assert (
            context.resources.io_manager._db_client.auth_resource.service_account_info  # noqa: SLF001
            is None
        )
        assert (
            context.resources.io_manager._db_client.auth_resource.service_account_file  # noqa: SLF001
            is None
        )
        return 1

    resource_defs = {
        "io_manager": FakeBigQueryIOManager(
            project=EnvVar("GCP_PROJECT_ID"), google_auth_resource=GoogleAuthResource()
        )
    }

    materialize(
        [test_asset],
        resources=resource_defs,
    )
