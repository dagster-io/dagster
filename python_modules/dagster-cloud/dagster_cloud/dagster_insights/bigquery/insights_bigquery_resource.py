from collections.abc import Iterator
from contextlib import contextmanager, nullcontext

from dagster import AssetObservation
from dagster._annotations import beta
from dagster_gcp import BigQueryResource
from dagster_gcp.bigquery.utils import setup_gcp_creds
from google.cloud import bigquery

from dagster_cloud.dagster_insights.bigquery.bigquery_utils import (
    build_bigquery_cost_metadata,
    marker_asset_key_for_job,
)
from dagster_cloud.dagster_insights.insights_utils import get_current_context_and_asset_key

OUTPUT_NON_ASSET_SIGIL = "__bigquery_query_metadata_"


class WrappedBigQueryClient(bigquery.Client):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._query_bytes = []
        self._query_slots_ms = []
        self._job_ids = []

    def query(self, *args, **kwargs) -> bigquery.QueryJob:
        bq_job = super().query(*args, **kwargs)
        self._query_bytes.append(bq_job.total_bytes_billed or 0)
        self._query_slots_ms.append(bq_job.slot_millis or 0)
        self._job_ids.append(bq_job.job_id)
        return bq_job

    @property
    def job_ids(self) -> list[str]:
        return self._job_ids

    @property
    def total_bytes_billed(self) -> int:
        return sum([x for x in self._query_bytes])

    @property
    def total_slots_ms(self) -> int:
        return sum([x for x in self._query_slots_ms])


@beta
class InsightsBigQueryResource(BigQueryResource):
    """A wrapper around :py:class:`BigQueryResource` which automatically collects metadata about
    BigQuery costs which can be attributed to Dagster jobs and assets.

    A simple example of loading data into BigQuery and subsequently querying that data is shown below:

    Examples:
        .. code-block:: python

            from dagster import job, op
            from dagster_gcp import BigQueryResource
            from dagster_insights import InsightsBigQueryResource

            @op
            def get_one(bigquery_resource: BigQueryResource):
                with bigquery_resource.get_client() as client:
                    client.query("SELECT * FROM my_dataset.my_table")

            @job
            def my_bigquery_job():
                get_one()

            my_bigquery_job.execute_in_process(
                resources={ "bigquery": InsightsBigQueryResource(project="my-project") }
            )
    """

    @contextmanager
    def get_client(self) -> Iterator[bigquery.Client]:
        context, asset_key = get_current_context_and_asset_key()

        with setup_gcp_creds(self.gcp_credentials) if self.gcp_credentials else nullcontext():
            client = WrappedBigQueryClient(project=self.project, location=self.location)

            yield client

            if not asset_key:
                asset_key = marker_asset_key_for_job(context.job_def)

            if client.total_bytes_billed or client.total_slots_ms:
                context.log_event(
                    AssetObservation(
                        asset_key=asset_key,
                        metadata=build_bigquery_cost_metadata(
                            client.job_ids, client.total_bytes_billed, client.total_slots_ms
                        ),
                    )
                )
