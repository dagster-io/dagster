import os
import uuid
from contextlib import contextmanager
from typing import Iterator
from unittest.mock import MagicMock, patch

import pandas
import pandas as pd
import pytest
from dagster import (
    IOManagerDefinition,
    MetadataValue,
    TableColumn,
    TableSchema,
    build_input_context,
    build_output_context,
)
from dagster._core.storage.db_io_manager import TableSlice
from dagster_snowflake import build_snowflake_io_manager
from dagster_snowflake.resources import SnowflakeResource
from dagster_snowflake_pandas import (
    SnowflakePandasIOManager,
    SnowflakePandasTypeHandler,
    snowflake_pandas_io_manager,
)
from dagster_snowflake_pandas.snowflake_pandas_type_handler import (
    _convert_string_to_timestamp,
    _convert_timestamp_to_string,
)
from dagster_tests.storage_tests.test_db_io_manager_type_handler import (
    DataFrameType,
    TemplateTypeHandlerTestSuite,
)
from pandas import DataFrame

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE snowflake DB")
class TestSnowflakePandasTypeHandler(TemplateTypeHandlerTestSuite):
    @property
    def df_format(self) -> DataFrameType:
        return DataFrameType.PANDAS

    @property
    def schema(self) -> str:
        return "SNOWFLAKE_IO_MANAGER_SCHEMA"

    @property
    def database(self) -> str:
        return "TEST_SNOWFLAKE_IO_MANAGER"

    @property
    def shared_buildkite_snowflake_config(self):
        return {
            "account": os.getenv("SNOWFLAKE_ACCOUNT", ""),
            "user": "BUILDKITE",
            "password": os.getenv("SNOWFLAKE_BUILDKITE_PASSWORD", ""),
        }

    @contextmanager
    def temporary_table_name(self) -> Iterator[str]:
        table_name = "test_io_manager_" + str(uuid.uuid4()).replace("-", "_")
        with self.get_db_connection() as conn:
            try:
                yield table_name
            finally:
                conn.execute(f"drop table {self.schema}.{table_name}")

    def io_managers(self):
        return [
            SnowflakePandasIOManager(
                database=self.database, **self.shared_buildkite_snowflake_config
            ),
            snowflake_pandas_io_manager.configured(
                {**self.shared_buildkite_snowflake_config, "database": self.database}
            ),
        ]

    @contextmanager
    def get_db_connection(self):
        snowflake_resource = SnowflakeResource(
            database=self.database, **self.shared_buildkite_snowflake_config
        )
        with snowflake_resource.get_connection() as conn:
            yield conn.cursor()

    def select_all_from_table(self, table_name) -> pd.DataFrame:
        with self.get_db_connection() as conn:
            return conn.execute(f"SELECT * FROM {self.schema}.{table_name}").fetch_pandas_all()


resource_config = {
    "database": "database_abc",
    "account": "account_abc",
    "user": "user_abc",
    "password": "password_abc",
    "warehouse": "warehouse_abc",
}


def test_handle_output():
    handler = SnowflakePandasTypeHandler()
    connection = MagicMock()
    df = DataFrame([{"col1": "a", "col2": 1}])
    output_context = build_output_context(
        resource_config={**resource_config, "time_data_to_string": False}
    )

    with patch("dagster_snowflake_pandas.snowflake_pandas_type_handler.write_pandas", MagicMock()):
        metadata = handler.handle_output(
            output_context,
            TableSlice(
                table="my_table",
                schema="my_schema",
                database="my_db",
                columns=None,
                partition_dimensions=[],
            ),
            df,
            connection,
        )

    assert metadata == {
        "dataframe_columns": MetadataValue.table_schema(
            TableSchema(columns=[TableColumn("col1", "object"), TableColumn("col2", "int64")])
        ),
        "row_count": 1,
    }


def test_load_input():
    with patch(
        "dagster_snowflake_pandas.snowflake_pandas_type_handler.pd.read_sql"
    ) as mock_read_sql:
        connection = MagicMock()
        mock_read_sql.return_value = DataFrame([{"COL1": "a", "COL2": 1}])

        handler = SnowflakePandasTypeHandler()
        input_context = build_input_context(
            resource_config={**resource_config, "time_data_to_string": False}
        )
        df = handler.load_input(
            input_context,
            TableSlice(
                table="my_table",
                schema="my_schema",
                database="my_db",
                columns=None,
                partition_dimensions=[],
            ),
            connection,
        )
        assert mock_read_sql.call_args_list[0][1]["sql"] == "SELECT * FROM my_db.my_schema.my_table"
        assert df.equals(DataFrame([{"col1": "a", "col2": 1}]))


def test_type_conversions():
    # no timestamp data
    no_time = pandas.Series([1, 2, 3, 4, 5])
    converted = _convert_string_to_timestamp(_convert_timestamp_to_string(no_time, None, "foo"))
    assert (converted == no_time).all()

    # timestamp data
    with_time = pandas.Series(
        [
            pandas.Timestamp("2017-01-01T12:30:45.35"),
            pandas.Timestamp("2017-02-01T12:30:45.35"),
            pandas.Timestamp("2017-03-01T12:30:45.35"),
        ]
    )
    time_converted = _convert_string_to_timestamp(
        _convert_timestamp_to_string(with_time, None, "foo")
    )

    assert (with_time == time_converted).all()

    # string that isn't a time
    string_data = pandas.Series(["not", "a", "timestamp"])

    assert (_convert_string_to_timestamp(string_data) == string_data).all()


def test_build_snowflake_pandas_io_manager():
    assert isinstance(
        build_snowflake_io_manager([SnowflakePandasTypeHandler()]), IOManagerDefinition
    )
    # test wrapping decorator to make sure that works as expected
    assert isinstance(snowflake_pandas_io_manager, IOManagerDefinition)
