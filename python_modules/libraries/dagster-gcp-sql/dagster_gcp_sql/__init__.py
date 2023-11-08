from dagster._core.libraries import DagsterLibraryRegistry

from .bigquery.bigquery_sql_type_handler import (
    BigQuerySqlIOManager as BigQuerySqlIOManager,
    BigQuerySqlTypeHandler as BigQuerySqlTypeHandler,
    bigquery_sql_io_manager as bigquery_sql_io_manager,
)
from .version import __version__

DagsterLibraryRegistry.register("dagster-gcp-pandas", __version__)
