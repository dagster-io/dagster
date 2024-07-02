from dagster._core.libraries import DagsterLibraryRegistry

from .version import __version__
from .bigquery.bigquery_pandas_type_handler import (
    BigQueryPandasIOManager as BigQueryPandasIOManager,
    BigQueryPandasTypeHandler as BigQueryPandasTypeHandler,
    bigquery_pandas_io_manager as bigquery_pandas_io_manager,
)

DagsterLibraryRegistry.register("dagster-gcp-pandas", __version__)
