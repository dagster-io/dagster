from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_deltalake_polars.deltalake_polars_type_handler import (
    DeltaLakePolarsIOManager as DeltaLakePolarsIOManager,
    DeltaLakePolarsTypeHandler as DeltaLakePolarsTypeHandler,
)
from dagster_deltalake_polars.version import __version__

DagsterLibraryRegistry.register("dagster-deltalake-polars", __version__)
