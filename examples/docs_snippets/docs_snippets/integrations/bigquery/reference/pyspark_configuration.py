from dagster import asset


@asset
def iris_data():
    return None


# start_configuration

from dagster_gcp_pyspark import BigQueryPySparkIOManager

from dagster import Definitions

defs = Definitions(
    assets=[iris_data],
    resources={
        "io_manager": BigQueryPySparkIOManager(
            project="my-gcp-project",  # required
            location="us-east5",  # optional, defaults to the default location for the project - see https://cloud.google.com/bigquery/docs/locations for a list of locations
            dataset="IRIS",  # optional, defaults to PUBLIC
            temporary_gcs_bucket="my-gcs-bucket",  # optional, defaults to None, which will result in a direct write to BigQuery
        )
    },
)

# end_configuration
