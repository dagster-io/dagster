from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_postgres_pandas.postgres_pandas_type_handler import (
    PostgresPandasIOManager as PostgresPandasIOManager,
    PostgresPandasTypeHandler as PostgresPandasTypeHandler,
    postgres_pandas_io_manager as postgres_pandas_io_manager,
)
from dagster_postgres_pandas.version import __version__

DagsterLibraryRegistry.register("dagster-postgres-pandas", __version__)
