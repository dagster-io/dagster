from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_deltalake_pandas.deltalake_pandas_type_handler import (
    DeltaLakePandasIOManager as DeltaLakePandasIOManager,
    DeltaLakePandasTypeHandler as DeltaLakePandasTypeHandler,
)
from dagster_deltalake_pandas.version import __version__

DagsterLibraryRegistry.register("dagster-deltalake-pandas", __version__)
