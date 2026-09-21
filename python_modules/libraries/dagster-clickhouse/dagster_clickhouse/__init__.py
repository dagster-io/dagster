from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_clickhouse.components import ClickhouseQueryComponent as ClickhouseQueryComponent
from dagster_clickhouse.db_client import (
    ClickhouseDbClient as ClickhouseDbClient,
    format_clickhouse_table_fqn as format_clickhouse_table_fqn,
)
from dagster_clickhouse.io_manager import (
    ClickhouseIOManager as ClickhouseIOManager,
    build_clickhouse_io_manager as build_clickhouse_io_manager,
)
from dagster_clickhouse.resource import ClickhouseResource as ClickhouseResource
from dagster_clickhouse.version import __version__

DagsterLibraryRegistry.register("dagster-clickhouse", __version__)

__all__ = [
    "ClickhouseDbClient",
    "ClickhouseIOManager",
    "ClickhouseQueryComponent",
    "ClickhouseResource",
    "build_clickhouse_io_manager",
    "format_clickhouse_table_fqn",
]
