from dagster._core.libraries import DagsterLibraryRegistry

from .io_manager import (
    DuckDBIOManager as DuckDBIOManager,
    build_duckdb_io_manager as build_duckdb_io_manager,
)
from .resource import DuckDBResource as DuckDBResource
from .version import __version__

DagsterLibraryRegistry.register("dagster-duckdb", __version__)
