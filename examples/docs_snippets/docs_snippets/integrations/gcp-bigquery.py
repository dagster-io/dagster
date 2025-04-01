from dagster_gcp import BigQueryResource

import dagster as dg


@dg.asset
def my_table(bigquery: BigQueryResource):
    with bigquery.get_client() as client:
        client.query("SELECT * FROM my_dataset.my_table")


defs = dg.Definitions(
    assets=[my_table], resources={"bigquery": BigQueryResource(project="my-project")}
)
