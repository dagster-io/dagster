from dagster_polars.io_managers.base import BasePolarsUPathIOManager
from dagster_polars.io_managers.parquet import PolarsParquetIOManager

__all__ = [
    "PolarsParquetIOManager",
    "BasePolarsUPathIOManager",
]


try:
    # provided by dagster-polars[delta]
    from dagster_polars.io_managers.delta import DeltaWriteMode, PolarsDeltaIOManager  # noqa

    __all__.extend(["DeltaWriteMode", "PolarsDeltaIOManager"])
except ImportError:
    pass


try:
    # provided by dagster-polars[gcp]
    from dagster_polars.io_managers.bigquery import (
        PolarsBigQueryIOManager,  # noqa: F401
        PolarsBigQueryTypeHandler,  # noqa: F401
    )

    __all__.extend(["PolarsBigQueryIOManager", "PolarsBigQueryTypeHandler"])
except ImportError:
    pass
