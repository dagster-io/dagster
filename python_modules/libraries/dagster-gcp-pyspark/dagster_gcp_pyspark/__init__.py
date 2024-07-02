from dagster._core.libraries import DagsterLibraryRegistry

from .version import __version__
from .bigquery.bigquery_pyspark_type_handler import (
    BigQueryPySparkIOManager as BigQueryPySparkIOManager,
    BigQueryPySparkTypeHandler as BigQueryPySparkTypeHandler,
    bigquery_pyspark_io_manager as bigquery_pyspark_io_manager,
)

DagsterLibraryRegistry.register("dagster-gcp-pyspark", __version__)
