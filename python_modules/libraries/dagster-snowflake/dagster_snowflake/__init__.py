from dagster._core.libraries import DagsterLibraryRegistry

from .resources import SnowflakeConnection, snowflake_resource
from .snowflake_io_manager import build_snowflake_io_manager
from .solids import snowflake_op_for_query
from .version import __version__

DagsterLibraryRegistry.register("dagster-snowflake", __version__)

__all__ = [
    "snowflake_op_for_query",
    "snowflake_resource",
    "build_snowflake_io_manager",
    "SnowflakeConnection",
]
