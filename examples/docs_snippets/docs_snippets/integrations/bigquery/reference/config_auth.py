from dagster import asset


@asset
def iris_data():
    return None


# start_example

from dagster_gcp_pandas import BigQueryPandasIOManager

from dagster import Definitions, EnvVar

defs = Definitions(
    assets=[iris_data],
    resources={
        "io_manager": BigQueryPandasIOManager(
            project="my-gcp-project",
            location="us-east5",
            dataset="IRIS",
            timeout=15.0,
            gcp_credentials=EnvVar("GCP_CREDS"),
        )
    },
)


# end_example
