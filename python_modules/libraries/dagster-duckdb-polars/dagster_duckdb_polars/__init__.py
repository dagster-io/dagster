from dagster._core.libraries import DagsterLibraryRegistry

from .version import __version__
from .duckdb_polars_type_handler import (
    DuckDBPolarsIOManager as DuckDBPolarsIOManager,
    DuckDBPolarsTypeHandler as DuckDBPolarsTypeHandler,
    duckdb_polars_io_manager as duckdb_polars_io_manager,
)

DagsterLibraryRegistry.register("dagster-duckdb-pandas", __version__)
