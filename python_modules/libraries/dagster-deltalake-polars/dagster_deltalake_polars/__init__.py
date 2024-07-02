from dagster._core.libraries import DagsterLibraryRegistry

from .version import __version__
from .deltalake_polars_type_handler import (
    DeltaLakePolarsIOManager as DeltaLakePolarsIOManager,
    DeltaLakePolarsTypeHandler as DeltaLakePolarsTypeHandler,
)

DagsterLibraryRegistry.register("dagster-deltalake-polars", __version__)
