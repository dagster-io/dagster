from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_duckdb_polars.duckdb_polars_type_handler import (
    DuckDBPolarsIOManager as DuckDBPolarsIOManager,
    DuckDBPolarsTypeHandler as DuckDBPolarsTypeHandler,
    duckdb_polars_io_manager as duckdb_polars_io_manager,
)
from dagster_duckdb_polars.version import __version__

DagsterLibraryRegistry.register("dagster-duckdb-pandas", __version__)
