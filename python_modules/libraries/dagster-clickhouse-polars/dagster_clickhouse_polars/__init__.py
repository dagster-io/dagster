from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_clickhouse_polars.clickhouse_polars_type_handler import (
    ClickhousePolarsIOManager as ClickhousePolarsIOManager,
    ClickhousePolarsTypeHandler as ClickhousePolarsTypeHandler,
    clickhouse_polars_io_manager as clickhouse_polars_io_manager,
)
from dagster_clickhouse_polars.version import __version__

DagsterLibraryRegistry.register("dagster-clickhouse-polars", __version__)

__all__ = [
    "ClickhousePolarsIOManager",
    "ClickhousePolarsTypeHandler",
    "clickhouse_polars_io_manager",
]
