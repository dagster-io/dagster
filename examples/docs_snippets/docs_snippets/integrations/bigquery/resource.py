from dagster_gcp import BigQueryResource

from dagster import Definitions, asset

# this example executes a query against the IRIS.IRIS_DATA table created in Step 2 of the
# Using Dagster with BigQuery tutorial


@asset
def small_petals(bigquery: BigQueryResource):
    with bigquery.get_client() as client:
        return client.query(
            'SELECT * FROM IRIS.IRIS_DATA WHERE "petal_length_cm" < 1 AND'
            ' "petal_width_cm" < 1',
        ).result()


defs = Definitions(
    assets=[small_petals],
    resources={
        "bigquery": BigQueryResource(
            project="my-gcp-project",
            location="us-east5",
        )
    },
)
