from dagster._core.utils import check_dagster_package_version

from .resources import SnowflakeConnection, snowflake_resource
from .snowflake_io_manager import build_snowflake_io_manager
from .solids import snowflake_op_for_query
from .version import __version__

check_dagster_package_version("dagster-snowflake", __version__)

__all__ = [
    "snowflake_op_for_query",
    "snowflake_resource",
    "build_snowflake_io_manager",
    "SnowflakeConnection",
]
