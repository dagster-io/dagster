from dagster._core.libraries import DagsterLibraryRegistry

from dagster_polars.io_managers.base import BasePolarsUPathIOManager
from dagster_polars.io_managers.parquet import PolarsParquetIOManager
from dagster_polars.types import DataFramePartitions, LazyFramePartitions
from dagster_polars.version import __version__

__all__ = [
    "PolarsParquetIOManager",
    "BasePolarsUPathIOManager",
    "DataFramePartitions",
    "LazyFramePartitions",
    "__version__",
]


try:
    # provided by dagster-polars[delta]
    from dagster_polars.io_managers.delta import DeltaWriteMode, PolarsDeltaIOManager  # noqa

    __all__.extend(["DeltaWriteMode", "PolarsDeltaIOManager"])
except ImportError:
    pass


try:
    # provided by dagster-polars[bigquery]
    from dagster_polars.io_managers.bigquery import (
        PolarsBigQueryIOManager,  # noqa
        PolarsBigQueryTypeHandler,  # noqa
    )

    __all__.extend(["PolarsBigQueryIOManager", "PolarsBigQueryTypeHandler"])
except ImportError:
    pass

DagsterLibraryRegistry.register("dagster-polars", __version__)
