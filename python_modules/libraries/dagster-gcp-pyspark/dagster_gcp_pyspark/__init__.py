from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_gcp_pyspark.bigquery.bigquery_pyspark_type_handler import (
    BigQueryPySparkIOManager as BigQueryPySparkIOManager,
    BigQueryPySparkTypeHandler as BigQueryPySparkTypeHandler,
    bigquery_pyspark_io_manager as bigquery_pyspark_io_manager,
)
from dagster_gcp_pyspark.version import __version__

DagsterLibraryRegistry.register("dagster-gcp-pyspark", __version__)
