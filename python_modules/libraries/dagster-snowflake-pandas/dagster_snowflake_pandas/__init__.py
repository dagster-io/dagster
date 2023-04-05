from dagster._core.libraries import DagsterLibraryRegistry

from .snowflake_pandas_type_handler import (
    SnowflakePandasIOManager as SnowflakePandasIOManager,
    SnowflakePandasTypeHandler as SnowflakePandasTypeHandler,
    snowflake_pandas_io_manager as snowflake_pandas_io_manager,
)
from .version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-snowflake-pandas", __version__)
