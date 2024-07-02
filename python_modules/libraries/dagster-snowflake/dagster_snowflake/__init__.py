from dagster._core.libraries import DagsterLibraryRegistry

from .ops import snowflake_op_for_query as snowflake_op_for_query
from .version import __version__
from .resources import (
    SnowflakeResource as SnowflakeResource,
    SnowflakeConnection as SnowflakeConnection,
    snowflake_resource as snowflake_resource,
    fetch_last_updated_timestamps as fetch_last_updated_timestamps,
)
from .snowflake_io_manager import (
    SnowflakeIOManager as SnowflakeIOManager,
    build_snowflake_io_manager as build_snowflake_io_manager,
)

DagsterLibraryRegistry.register("dagster-snowflake", __version__)
