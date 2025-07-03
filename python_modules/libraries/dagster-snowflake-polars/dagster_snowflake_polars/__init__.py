from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_snowflake_polars.snowflake_polars_type_handler import (
    SnowflakePolarsIOManager as SnowflakePolarsIOManager,
    SnowflakePolarsTypeHandler as SnowflakePolarsTypeHandler,
    snowflake_polars_io_manager as snowflake_polars_io_manager,
)
from dagster_snowflake_polars.version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-snowflake-polars", __version__)
