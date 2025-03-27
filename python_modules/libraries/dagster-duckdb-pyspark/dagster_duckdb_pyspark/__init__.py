from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_duckdb_pyspark.duckdb_pyspark_type_handler import (
    DuckDBPySparkIOManager as DuckDBPySparkIOManager,
    DuckDBPySparkTypeHandler as DuckDBPySparkTypeHandler,
    duckdb_pyspark_io_manager as duckdb_pyspark_io_manager,
)
from dagster_duckdb_pyspark.version import __version__

DagsterLibraryRegistry.register("dagster-duckdb-pyspark", __version__)
