from dagster._core.libraries import DagsterLibraryRegistry

from .version import __version__
from .duckdb_pyspark_type_handler import (
    DuckDBPySparkIOManager as DuckDBPySparkIOManager,
    DuckDBPySparkTypeHandler as DuckDBPySparkTypeHandler,
    duckdb_pyspark_io_manager as duckdb_pyspark_io_manager,
)

DagsterLibraryRegistry.register("dagster-duckdb-pyspark", __version__)
