from dagster_polars.io_managers.base import BasePolarsUPathIOManager
from dagster_polars.io_managers.parquet import PolarsParquetIOManager
from dagster_polars.types import (
    DataFramePartitions,
    DataFramePartitionsWithMetadata,
    DataFrameWithMetadata,
    LazyFramePartitions,
    LazyFramePartitionsWithMetadata,
    LazyFrameWithMetadata,
    StorageMetadata,
)
from dagster_polars.version import __version__

__all__ = [
    "PolarsParquetIOManager",
    "BasePolarsUPathIOManager",
    "StorageMetadata",
    "DataFrameWithMetadata",
    "LazyFrameWithMetadata",
    "DataFramePartitions",
    "LazyFramePartitions",
    "DataFramePartitionsWithMetadata",
    "LazyFramePartitionsWithMetadata",
    "__version__",
]


try:
    from dagster_polars.io_managers.delta import DeltaWriteMode, PolarsDeltaIOManager  # noqa

    __all__.extend(["DeltaWriteMode", "PolarsDeltaIOManager"])
except ImportError:
    pass


try:
    from dagster_polars.io_managers.bigquery import BigQueryPolarsIOManager  # noqa

    __all__.extend(["BigQueryPolarsIOManager"])
except ImportError:
    pass
