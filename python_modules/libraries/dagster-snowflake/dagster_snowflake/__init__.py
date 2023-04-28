from dagster._core.libraries import DagsterLibraryRegistry

from .ops import snowflake_op_for_query as snowflake_op_for_query
from .resources import (
    SnowflakeConnection as SnowflakeConnection,
    SnowflakeResource as SnowflakeResource,
    snowflake_resource as snowflake_resource,
)
from .snowflake_io_manager import (
    SnowflakeIOManager as SnowflakeIOManager,
    build_snowflake_io_manager as build_snowflake_io_manager,
)
from .version import __version__

DagsterLibraryRegistry.register("dagster-snowflake", __version__)
