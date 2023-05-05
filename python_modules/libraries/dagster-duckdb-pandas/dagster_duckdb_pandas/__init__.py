from dagster._core.libraries import DagsterLibraryRegistry

from .duckdb_pandas_type_handler import (
    DuckDBPandasIOManager as DuckDBPandasIOManager,
    DuckDBPandasTypeHandler as DuckDBPandasTypeHandler,
    duckdb_pandas_io_manager as duckdb_pandas_io_manager,
)
from .version import __version__

DagsterLibraryRegistry.register("dagster-duckdb-pandas", __version__)
