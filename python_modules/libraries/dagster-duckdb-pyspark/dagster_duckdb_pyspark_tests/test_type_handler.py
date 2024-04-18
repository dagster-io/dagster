import uuid
from contextlib import contextmanager
from typing import Iterator

import duckdb
import pandas as pd
from dagster._core.test_utils import ensure_dagster_tests_import
from dagster_duckdb_pyspark import DuckDBPySparkIOManager, duckdb_pyspark_io_manager

ensure_dagster_tests_import()
from dagster_tests.storage_tests.test_db_io_manager_type_handler import (
    DataFrameType,
    TemplateTypeHandlerTestSuite,
)
from pyspark.sql import (
    SparkSession,
)


class TestDuckDBPySparkTypeHandler(TemplateTypeHandlerTestSuite):
    @property
    def df_format(self) -> DataFrameType:
        return DataFrameType.PYSPARK

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
            duckdb_pyspark_io_manager.configured({"database": "unit_test.duckdb"}),
            DuckDBPySparkIOManager(database="unit_test.duckdb"),
        ]

    @contextmanager
    def get_db_connection(self):
        conn = duckdb.connect(database="unit_test.duckdb")
        yield conn
        conn.close()

    def select_all_from_table(self, table_name) -> pd.DataFrame:
        with self.get_db_connection() as conn:
            return conn.execute(f"SELECT * FROM {self.schema}.{table_name}").fetch_df()

    def _setup_spark_session(self):
        return SparkSession.builder.getOrCreate()
