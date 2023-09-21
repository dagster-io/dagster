from dagster import asset


@asset
def iris_data():
    return None


# start_example

from dagster_gcp import BigQueryResource

from dagster import Definitions

defs = Definitions(
    assets=[iris_data],
    resources={
        "bigquery": BigQueryResource(
            project="my-gcp-project",  # required
            location="us-east5",  # optional, defaults to the default location for the project - see https://cloud.google.com/bigquery/docs/locations for a list of locations
        )
    },
)


# end_example
