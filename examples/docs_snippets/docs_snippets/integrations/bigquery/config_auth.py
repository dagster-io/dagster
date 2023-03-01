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
                "project": "my-gcp-project",
                "location": "us-east5",
                "dataset": "IRIS",
                "gcp_credential": {"env": "GCP_CREDS"},
            }
        )
    },
)


# end_example
