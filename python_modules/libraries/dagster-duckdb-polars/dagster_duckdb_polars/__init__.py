from dagster._core.libraries import DagsterLibraryRegistry

from .duckdb_polars_type_handler import (
    DuckDBPolarsIOManager as DuckDBPolarsIOManager,
    DuckDBPolarsTypeHandler as DuckDBPolarsTypeHandler,
    duckdb_polars_io_manager as duckdb_polars_io_manager,
)
from .version import __version__

DagsterLibraryRegistry.register("dagster-duckdb-pandas", __version__)
