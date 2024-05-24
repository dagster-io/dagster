from dagster._core.libraries import DagsterLibraryRegistry

from .deltalake_pandas_type_handler import (
    DeltaLakePandasIOManager as DeltaLakePandasIOManager,
    DeltaLakePandasTypeHandler as DeltaLakePandasTypeHandler,
)
from .version import __version__

DagsterLibraryRegistry.register("dagster-deltalake-pandas", __version__)
