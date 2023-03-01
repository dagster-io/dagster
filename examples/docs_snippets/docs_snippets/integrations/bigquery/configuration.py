from dagster import asset


@asset
def iris_data():
    return None


# start_example

from dagster_gcp_pandas import bigquery_pandas_io_manager

from dagster import Definitions

defs = Definitions(
    assets=[iris_data],
    resources={
        "io_manager": bigquery_pandas_io_manager.configured(
            {
                "project": "my-gcp-project",  # required
                "location": "us-east5",  # optional, defaults to the default location for the project - see https://cloud.google.com/bigquery/docs/locations for a list of locations
                "dataset": "IRIS",  # optional, defaults to PUBLIC
                "timeout": 15.0,  # optional, defaults to None
                "retries": 2,  # optional, defaults to BigQuery default
            }
        )
    },
)


# end_example
