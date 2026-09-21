from dagster_cloud.dagster_insights import InsightsBigQueryResource

import dagster as dg


@dg.asset
# highlight-start
def bigquery_datasets(bigquery: InsightsBigQueryResource):
    # highlight-end
    with bigquery.get_client() as client:
        return client.list_datasets()


defs = dg.Definitions(
    assets=[bigquery_datasets],
    resources={
        # highlight-start
        "bigquery": InsightsBigQueryResource(project="my-project"),
        # highlight-end
    },
)
