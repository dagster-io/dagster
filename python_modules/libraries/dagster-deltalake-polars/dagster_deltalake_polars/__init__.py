from dagster._core.libraries import DagsterLibraryRegistry

from .deltalake_polars_type_handler import (
    DeltaLakePolarsIOManager as DeltaLakePolarsIOManager,
    DeltaLakePolarsTypeHandler as DeltaLakePolarsTypeHandler,
)
from .version import __version__

DagsterLibraryRegistry.register("dagster-deltalake-polars", __version__)
