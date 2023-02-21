iris_data = None
rose_data = None

# start_example

from dagster_gcp import build_bigquery_io_manager
from dagster_gcp_pandas import BigQueryPandasTypeHandler
from dagster_gcp_pyspark import BigQueryPySparkTypeHandler

from dagster import Definitions

bigquery_io_manager = build_bigquery_io_manager(
    [BigQueryPandasTypeHandler(), BigQueryPySparkTypeHandler()]
)

defs = Definitions(
    assets=[iris_data, rose_data],  # type: ignore  # (didactic)
    resources={
        "io_manager": bigquery_io_manager.configured(
            {
                "project": "my-gcp-project",
                "data": "IRIS",
            }
        )
    },
)


# end_example
