from dagster._core.libraries import DagsterLibraryRegistry

from .version import __version__
from .deltalake_pandas_type_handler import (
    DeltaLakePandasIOManager as DeltaLakePandasIOManager,
    DeltaLakePandasTypeHandler as DeltaLakePandasTypeHandler,
)

DagsterLibraryRegistry.register("dagster-deltalake-pandas", __version__)
