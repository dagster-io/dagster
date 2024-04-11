import os
import uuid
from contextlib import contextmanager
from typing import Iterator

import pandas as pd
import pandas_gbq
from dagster import (
    EnvVar,
)
from dagster_gcp_pyspark import (
    BigQueryPySparkIOManager,
    bigquery_pyspark_io_manager,
)
from dagster_tests.storage_tests.test_db_io_manager_type_handler import (
    DataFrameType,
    TemplateTypeHandlerTestSuite,
)
from google.cloud import bigquery

resource_config = {
    "database": "database_abc",
    "account": "account_abc",
    "user": "user_abc",
    "password": "password_abc",
    "warehouse": "warehouse_abc",
}

IS_BUILDKITE = os.getenv("BUILDKITE") is not None

SHARED_BUILDKITE_BQ_CONFIG = {
    "project": os.getenv("GCP_PROJECT_ID"),
    "temporary_gcs_bucket": "gcs_io_manager_test",
}

SCHEMA = "BIGQUERY_IO_MANAGER_SCHEMA"

pythonic_bigquery_io_manager = BigQueryPySparkIOManager(
    project=EnvVar("GCP_PROJECT_ID"), temporary_gcs_bucket="gcs_io_manager_test"
)
old_bigquery_io_manager = bigquery_pyspark_io_manager.configured(SHARED_BUILDKITE_BQ_CONFIG)


class TestDuckDBPySparkTypeHandler(TemplateTypeHandlerTestSuite):
    @property
    def df_format(self) -> DataFrameType:
        return DataFrameType.PYSPARK

    @property
    def schema(self) -> str:
        return "BIGQUERY_IO_MANAGER_SCHEMA"

    @property
    def shared_buildkite_bigquery_config(self):
        return {
            "project": os.getenv("GCP_PROJECT_ID"),
        }

    @contextmanager
    def temporary_table_name(self) -> Iterator[str]:
        with self.get_db_connection() as conn:
            table_name = "test_io_manager_" + str(uuid.uuid4()).replace("-", "_")
            try:
                yield table_name
            finally:
                conn.query(
                    f"drop table {self.shared_buildkite_bigquery_config['project']}.{self.schema}.{table_name}"
                ).result()

    def io_managers(self):
        return [
            BigQueryPySparkIOManager(
                project=EnvVar("GCP_PROJECT_ID"),
            ),
            bigquery_pyspark_io_manager.configured(self.shared_buildkite_bigquery_config),
        ]

    @contextmanager
    def get_db_connection(self):
        yield bigquery.Client(
            project=self.shared_buildkite_bigquery_config["project"],
        )

    def select_all_from_table(self, table_name) -> pd.DataFrame:
        return pandas_gbq.read_gbq(
            f"SELECT * FROM {self.schema}.{table_name}",
            project_id=self.shared_buildkite_bigquery_config["project"],
        )

    def _setup_spark_session(self, spark):
        return spark
