import os
import uuid
from contextlib import contextmanager
from typing import Iterator

from google.cloud import bigquery

IS_BUILDKITE = os.getenv("BUILDKITE") is not None

SHARED_BUILDKITE_BQ_CONFIG = {
    "project": os.getenv("GCP_PROJECT_ID"),
}


@contextmanager
def temporary_bigquery_table(schema_name: str, column_str: str) -> Iterator[str]:
    bq_client = bigquery.Client(
        project=SHARED_BUILDKITE_BQ_CONFIG["project"],
    )
    table_name = "test_io_manager_" + str(uuid.uuid4()).replace("-", "_")
    bq_client.query(f"create table {schema_name}.{table_name} ({column_str})").result()
    try:
        yield table_name
    finally:
        bq_client.query(
            f"drop table {SHARED_BUILDKITE_BQ_CONFIG['project']}.{schema_name}.{table_name}"
        ).result()
