import re
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from datetime import datetime
from typing import Any

from dagster import (
    ConfigurableResource,
    IAttachDifferentObjectToOpContext,
    _check as check,
    resource,
)
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from dagster._core.storage.db_io_manager import check_sql_identifier
from google.cloud import bigquery
from pydantic import Field

from dagster_gcp.bigquery.utils import setup_gcp_creds


class BigQueryResource(ConfigurableResource, IAttachDifferentObjectToOpContext):
    """Resource for interacting with Google BigQuery.

    Examples:
        .. code-block:: python

            from dagster import Definitions, asset
            from dagster_gcp import BigQueryResource

            @asset
            def my_table(bigquery: BigQueryResource):
                with bigquery.get_client() as client:
                    client.query("SELECT * FROM my_dataset.my_table")

            defs = Definitions(
                assets=[my_table],
                resources={
                    "bigquery": BigQueryResource(project="my-project")
                }
            )
    """

    project: str | None = Field(
        default=None,
        description=(
            "Project ID for the project which the client acts on behalf of. Will be passed when"
            " creating a dataset / job. If not passed, falls back to the default inferred from the"
            " environment."
        ),
    )

    location: str | None = Field(
        default=None,
        description="Default location for jobs / datasets / tables.",
    )

    gcp_credentials: str | None = Field(
        default=None,
        description=(
            "GCP authentication credentials. If provided, a temporary file will be created"
            " with the credentials and ``GOOGLE_APPLICATION_CREDENTIALS`` will be set to the"
            " temporary file. To avoid issues with newlines in the keys, you must base64"
            " encode the key. You can retrieve the base64 encoded key with this shell"
            " command: ``cat $GOOGLE_AUTH_CREDENTIALS | base64``"
        ),
    )

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @contextmanager
    def get_client(self) -> Iterator[bigquery.Client]:
        """Context manager to create a BigQuery Client.

        Examples:
            .. code-block:: python

                from dagster import asset
                from dagster_gcp import BigQueryResource

                @asset
                def my_table(bigquery: BigQueryResource):
                    with bigquery.get_client() as client:
                        client.query("SELECT * FROM my_dataset.my_table")
        """
        if self.gcp_credentials:
            with setup_gcp_creds(self.gcp_credentials):
                yield bigquery.Client(project=self.project, location=self.location)

        else:
            yield bigquery.Client(project=self.project, location=self.location)

    def get_object_to_set_on_execution_context(self) -> Any:
        with self.get_client() as client:
            yield client


@dagster_maintained_resource
@resource(
    config_schema=BigQueryResource.to_config_schema(),
    description="Dagster resource for connecting to BigQuery",
)
def bigquery_resource(context):
    bq_resource = BigQueryResource.from_resource_context(context)
    with bq_resource.get_client() as client:
        yield client


# An optional project id and a dataset. A bare project id may contain hyphens, but not "--",
# which starts a comment; a backtick-quoted one may also be domain-scoped ("example.com:proj").
DATASET_ID_REGEX = re.compile(r"(?:(?:[^\W\d]\w*(?:-\w+)*|`[\w.:-]+`)\.)?\w+")


def fetch_last_updated_timestamps(
    *,
    client: bigquery.Client,
    dataset_id: str,
    table_ids: Sequence[str],
) -> Mapping[str, datetime]:
    """Get the last updated timestamps of a list BigQuery table.

    Note that this only works on BigQuery tables, and not views.

    Args:
        client (bigquery.Client): The BigQuery client.
        dataset_id (str): The BigQuery dataset ID.
        table_ids (Sequence[str]): The table IDs to get the last updated timestamp for.

    Returns:
        Mapping[str, datetime]: A mapping of table IDs to their last updated timestamps (UTC).
    """
    check.invariant(
        len(table_ids) > 0,
        "At least one table ID must be provided.",
    )
    check_sql_identifier(dataset_id, field="dataset_id", pattern=DATASET_ID_REGEX)
    query = f"""
        SELECT
            table_id,
            TIMESTAMP_MILLIS(last_modified_time) as last_modified_time
        FROM
            {dataset_id}.__TABLES__
        WHERE
            table_id IN UNNEST(@table_ids)
    """

    query_job = client.query(
        query,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[bigquery.ArrayQueryParameter("table_ids", "STRING", list(table_ids))]
        ),
    )
    results = query_job.result()
    modified_times = {row.table_id: row.last_modified_time for row in results}

    for table_id in table_ids:
        if table_id not in modified_times:
            raise ValueError(f"Table {table_id} not found in dataset {dataset_id}")

    return modified_times
