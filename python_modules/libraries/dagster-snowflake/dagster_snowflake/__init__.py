from dagster.core.utils import check_dagster_package_version

from .resources import SnowflakeConnection, snowflake_resource
from .solids import snowflake_solid_for_query
from .version import __version__

check_dagster_package_version("dagster-snowflake", __version__)

__all__ = ["snowflake_solid_for_query", "snowflake_resource", "SnowflakeConnection"]
