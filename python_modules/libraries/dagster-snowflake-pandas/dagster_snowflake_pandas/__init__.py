from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_snowflake_pandas.snowflake_pandas_type_handler import (
    SnowflakePandasIOManager as SnowflakePandasIOManager,
    SnowflakePandasTypeHandler as SnowflakePandasTypeHandler,
    snowflake_pandas_io_manager as snowflake_pandas_io_manager,
)
from dagster_snowflake_pandas.version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-snowflake-pandas", __version__)
