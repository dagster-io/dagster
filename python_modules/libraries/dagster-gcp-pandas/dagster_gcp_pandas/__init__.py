from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_gcp_pandas.bigquery.bigquery_pandas_type_handler import (
    BigQueryPandasIOManager as BigQueryPandasIOManager,
    BigQueryPandasTypeHandler as BigQueryPandasTypeHandler,
    bigquery_pandas_io_manager as bigquery_pandas_io_manager,
)
from dagster_gcp_pandas.version import __version__

DagsterLibraryRegistry.register("dagster-gcp-pandas", __version__)
