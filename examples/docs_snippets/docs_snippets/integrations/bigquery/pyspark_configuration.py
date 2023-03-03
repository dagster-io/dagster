iris_data = None

# start_configuration

from dagster_gcp_pyspark import bigquery_pyspark_io_manager

from dagster import Definitions

defs = Definitions(
    assets=[iris_data],  # type: ignore  # (didactic)
    resources={
        "io_manager": bigquery_pyspark_io_manager.configured(
            {
                "project": "my-gcp-project",  # required
                "location": "us-east5",  # optional, defaults to the default location for the project - see https://cloud.google.com/bigquery/docs/locations for a list of locations
                "data": "IRIS",  # optional, defaults to PUBLIC
                "temporary_gcs_bucket": "my-gcs-bucket",
            }
        )
    },
)

# end_configuration
