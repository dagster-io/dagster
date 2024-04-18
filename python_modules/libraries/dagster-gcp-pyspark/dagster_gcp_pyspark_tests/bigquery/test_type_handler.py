import os
import tempfile
import uuid
from contextlib import contextmanager
from typing import Iterator

import pandas as pd
import pandas_gbq
import requests
from dagster import (
    EnvVar,
)
from dagster._core.test_utils import ensure_dagster_tests_import
from dagster_gcp_pyspark import (
    BigQueryPySparkIOManager,
    bigquery_pyspark_io_manager,
)

ensure_dagster_tests_import()
import pytest
from dagster_tests.storage_tests.test_db_io_manager_type_handler import (
    DataFrameType,
    TemplateTypeHandlerTestSuite,
)
from google.cloud import bigquery
from pyspark.sql import (
    SparkSession,
)

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


BIGQUERY_JARS = "com.google.cloud.spark:spark-bigquery-with-dependencies_2.12:0.28.0"


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE bigquery DB")
class TestBigQueryPySparkTypeHandler(TemplateTypeHandlerTestSuite):
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

    def _setup_spark_session(self):
        # the shaded gcs connector jar is required to avoid dependency conflicts with the bigquery connector jar
        # however, the shaded jar cannot be automatically downloaded from the maven central repository when setting up
        # the spark session. So we download the jar ourselves
        jar_name = "gcs-connector-hadoop2-2.2.11-shaded.jar"
        jar_path = f"https://repo1.maven.org/maven2/com/google/cloud/bigdataoss/gcs-connector/hadoop2-2.2.11/{jar_name}"
        r = requests.get(jar_path)
        with tempfile.NamedTemporaryFile(delete_on_close=False) as local_jar_file:
            local_jar_file.write(r.content)

        spark = (
            SparkSession.builder.config(
                key="spark.jars.packages",
                value=BIGQUERY_JARS,
            )
            .config(key="spark.jars", value=local_jar_file)
            .getOrCreate()
        )

        # required config for the gcs connector
        spark._jsc.hadoopConfiguration().set(  # noqa: SLF001
            "fs.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem"
        )
        spark._jsc.hadoopConfiguration().set(  # noqa: SLF001
            "fs.gs.auth.service.account.enable", "true"
        )
        spark._jsc.hadoopConfiguration().set(  # noqa: SLF001
            "google.cloud.auth.service.account.json.keyfile",
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
        )

        return spark
