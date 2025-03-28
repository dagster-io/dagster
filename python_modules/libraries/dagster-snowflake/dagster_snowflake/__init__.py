from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_snowflake.ops import snowflake_op_for_query as snowflake_op_for_query
from dagster_snowflake.resources import (
    SnowflakeConnection as SnowflakeConnection,
    SnowflakeResource as SnowflakeResource,
    fetch_last_updated_timestamps as fetch_last_updated_timestamps,
    snowflake_resource as snowflake_resource,
)
from dagster_snowflake.snowflake_io_manager import (
    SnowflakeIOManager as SnowflakeIOManager,
    build_snowflake_io_manager as build_snowflake_io_manager,
)
from dagster_snowflake.version import __version__

DagsterLibraryRegistry.register("dagster-snowflake", __version__)
