from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_duckdb.io_manager import (
    DuckDBIOManager as DuckDBIOManager,
    build_duckdb_io_manager as build_duckdb_io_manager,
)
from dagster_duckdb.resource import DuckDBResource as DuckDBResource
from dagster_duckdb.version import __version__

DagsterLibraryRegistry.register("dagster-duckdb", __version__)
