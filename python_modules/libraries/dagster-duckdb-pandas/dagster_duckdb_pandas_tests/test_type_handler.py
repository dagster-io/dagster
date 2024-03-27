import os
import uuid
from contextlib import contextmanager
from typing import Iterator

import duckdb
import pandas as pd
import pytest
from dagster import (
    asset,
    materialize,
)
from dagster_duckdb_pandas import DuckDBPandasIOManager, duckdb_pandas_io_manager
from dagster_tests.storage_tests.test_db_io_manager_type_handler import (
    DataFrameType,
    TemplateTypeHandlerTestSuite,
)


class TestDuckDBPandasTypeHandler(TemplateTypeHandlerTestSuite):
    @property
    def df_format(self) -> DataFrameType:
        return DataFrameType.PANDAS

    @property
    def schema(self) -> str:
        return "the_schema"

    @contextmanager
    def temporary_table_name(self) -> Iterator[str]:
        table_name = "test_io_manager_" + str(uuid.uuid4()).replace("-", "_")
        try:
            yield table_name
        finally:
            with self.get_db_connection() as conn:
                conn.execute(f"DELETE FROM {self.schema}.{table_name}")

    def io_managers(self):
        return [
            duckdb_pandas_io_manager.configured({"database": "unit_test.duckdb"}),
            DuckDBPandasIOManager(database="unit_test.duckdb"),
        ]

    @contextmanager
    def get_db_connection(self):
        conn = duckdb.connect(database="unit_test.duckdb")
        yield conn
        conn.close()

    def select_all_from_table(self, table_name) -> pd.DataFrame:
        with self.get_db_connection() as conn:
            return conn.execute(f"SELECT * FROM {self.schema}.{table_name}").fetch_df()


@pytest.fixture(scope="session")
def all_io_managers(tmp_path):
    return [
        duckdb_pandas_io_manager.configured(
            {"database": os.path.join(tmp_path, "unit_test.duckdb")}
        ),
        DuckDBPandasIOManager(database=os.path.join(tmp_path, "unit_test.duckdb")),
    ]


def test_duckdb_io_manager_with_schema(tmp_path):
    @asset
    def my_df() -> pd.DataFrame:
        return pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

    @asset
    def my_df_plus_one(my_df: pd.DataFrame) -> pd.DataFrame:
        return my_df + 1

    schema_io_managers = [
        duckdb_pandas_io_manager.configured(
            {"database": os.path.join(tmp_path, "unit_test.duckdb"), "schema": "custom_schema"}
        ),
        DuckDBPandasIOManager(
            database=os.path.join(tmp_path, "unit_test.duckdb"), schema="custom_schema"
        ),
    ]

    for io_manager in schema_io_managers:
        resource_defs = {"io_manager": io_manager}

        # materialize asset twice to ensure that tables get properly deleted
        for _ in range(2):
            res = materialize([my_df, my_df_plus_one], resources=resource_defs)
            assert res.success

            duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))

            out_df = duckdb_conn.execute("SELECT * FROM custom_schema.my_df").fetch_df()
            assert out_df["a"].tolist() == [1, 2, 3]

            out_df = duckdb_conn.execute("SELECT * FROM custom_schema.my_df_plus_one").fetch_df()
            assert out_df["a"].tolist() == [2, 3, 4]

            duckdb_conn.close()
