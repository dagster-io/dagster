from dagster_gcp import BigQueryResource

import dagster as dg


@dg.asset
def bigquery_datasets(bigquery: BigQueryResource):
    with bigquery.get_client() as client:
        return client.list_datasets()


defs = dg.Definitions(
    assets=[bigquery_datasets],
    resources={
        "bigquery": BigQueryResource(project="my-project"),
    },
)
