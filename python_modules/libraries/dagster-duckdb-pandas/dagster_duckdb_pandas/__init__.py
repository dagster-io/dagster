from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_duckdb_pandas.duckdb_pandas_type_handler import (
    DuckDBPandasIOManager as DuckDBPandasIOManager,
    DuckDBPandasTypeHandler as DuckDBPandasTypeHandler,
    duckdb_pandas_io_manager as duckdb_pandas_io_manager,
)
from dagster_duckdb_pandas.version import __version__

DagsterLibraryRegistry.register("dagster-duckdb-pandas", __version__)
