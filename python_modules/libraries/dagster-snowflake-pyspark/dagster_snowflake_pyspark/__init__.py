from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_snowflake_pyspark.snowflake_pyspark_type_handler import (
    SnowflakePySparkIOManager as SnowflakePySparkIOManager,
    SnowflakePySparkTypeHandler as SnowflakePySparkTypeHandler,
    snowflake_pyspark_io_manager as snowflake_pyspark_io_manager,
)
from dagster_snowflake_pyspark.version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-snowflake-pyspark", __version__)
