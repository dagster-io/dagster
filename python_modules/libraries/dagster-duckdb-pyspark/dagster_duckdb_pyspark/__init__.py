from dagster._core.libraries import DagsterLibraryRegistry

from .duckdb_pyspark_type_handler import (
    DuckDBPySparkIOManager as DuckDBPySparkIOManager,
    DuckDBPySparkTypeHandler as DuckDBPySparkTypeHandler,
    duckdb_pyspark_io_manager as duckdb_pyspark_io_manager,
)
from .version import __version__

DagsterLibraryRegistry.register("dagster-duckdb-pyspark", __version__)
