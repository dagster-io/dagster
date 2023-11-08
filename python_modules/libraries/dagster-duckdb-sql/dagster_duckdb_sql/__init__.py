from dagster._core.libraries import DagsterLibraryRegistry

from .duckdb_sql_type_handler import (
    DuckDBSqlIOManager as DuckDBSqlIOManager,
    DuckDBSqlTypeHandler as DuckDBSqlTypeHandler,
    duckdb_sql_io_manager as duckdb_sql_io_manager,
)
from .version import __version__

DagsterLibraryRegistry.register("dagster-duckdb-sql", __version__)
