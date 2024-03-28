import os
import uuid
from contextlib import contextmanager
from typing import Iterator, Optional

import pandas as pd
import pandas_gbq
import pytest
from dagster import (
    EnvVar,
    Out,
    job,
    op,
)
from dagster_gcp_pandas import BigQueryPandasIOManager, bigquery_pandas_io_manager
from dagster_tests.storage_tests.test_db_io_manager_type_handler import (
    DataFrameType,
    TemplateTypeHandlerTestSuite,
)
from google.cloud import bigquery

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE bigquery DB")
class TestBigQueryPandasTypeHandler(TemplateTypeHandlerTestSuite):
    @property
    def df_format(self) -> DataFrameType:
        return DataFrameType.PANDAS

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
            BigQueryPandasIOManager(
                project=EnvVar("GCP_PROJECT_ID"),
            ),
            bigquery_pandas_io_manager.configured(self.shared_buildkite_bigquery_config),
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


SHARED_BUILDKITE_BQ_CONFIG = {
    "project": os.getenv("GCP_PROJECT_ID"),
}

SCHEMA = "BIGQUERY_IO_MANAGER_SCHEMA"

pythonic_bigquery_io_manager = BigQueryPandasIOManager(
    project=EnvVar("GCP_PROJECT_ID"),
)
old_bigquery_io_manager = bigquery_pandas_io_manager.configured(SHARED_BUILDKITE_BQ_CONFIG)


@contextmanager
def temporary_bigquery_table(schema_name: Optional[str]) -> Iterator[str]:
    bq_client = bigquery.Client(
        project=SHARED_BUILDKITE_BQ_CONFIG["project"],
    )
    table_name = "test_io_manager_" + str(uuid.uuid4()).replace("-", "_")
    try:
        yield table_name
    finally:
        bq_client.query(
            f"drop table {SHARED_BUILDKITE_BQ_CONFIG['project']}.{schema_name}.{table_name}"
        ).result()


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE bigquery DB")
@pytest.mark.parametrize("io_manager", [(old_bigquery_io_manager), (pythonic_bigquery_io_manager)])
@pytest.mark.integration
def test_io_manager_with_timestamp_conversion(io_manager):
    with temporary_bigquery_table(schema_name=SCHEMA) as table_name:
        time_df = pd.DataFrame(
            {
                "foo": ["bar", "baz"],
                "date": [
                    pd.Timestamp("2017-01-01T12:30:45.350"),
                    pd.Timestamp("2017-02-01T12:30:45.350"),
                ],
            }
        )

        @op(out={table_name: Out(io_manager_key="bigquery", metadata={"schema": SCHEMA})})
        def emit_time_df(_):
            return time_df

        @op
        def read_time_df(df: pd.DataFrame):
            assert set(df.columns) == {"foo", "date"}
            assert (df["date"] == time_df["date"]).all()

        @job(
            resource_defs={"bigquery": io_manager},
        )
        def io_manager_timestamp_test_job():
            read_time_df(emit_time_df())

        res = io_manager_timestamp_test_job.execute_in_process()
        assert res.success
