from dagster._core.libraries import DagsterLibraryRegistry

from .version import __version__
from .resource import DuckDBResource as DuckDBResource
from .io_manager import (
    DuckDBIOManager as DuckDBIOManager,
    build_duckdb_io_manager as build_duckdb_io_manager,
)

DagsterLibraryRegistry.register("dagster-duckdb", __version__)
