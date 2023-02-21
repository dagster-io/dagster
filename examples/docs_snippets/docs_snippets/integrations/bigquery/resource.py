from dagster_gcp import bigquery_resource

from dagster import Definitions, asset

# this example executes a query against the IRIS.IRIS_DATA table created in Step 2 of the
# Using Dagster with BigQuery tutorial


@asset(required_resource_keys={"bigquery"})
def small_petals(context):
    return context.resources.bigquery.query(
        'SELECT * FROM IRIS.IRIS_DATA WHERE "Petal length (cm)" < 1 AND "Petal width (cm)" < 1',
    ).result()


defs = Definitions(
    assets=[small_petals],
    resources={
        "snowflake": bigquery_resource.configured(
            {
                "project": "my-gcp-project",
                "location": "us-east5",
            }
        )
    },
)
