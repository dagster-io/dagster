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
except ImportError as e:
    if "deltalake" in str(e):
        pass
    else:
        raise e


try:
    # provided by dagster-polars[bigquery]
    from dagster_polars.io_managers.bigquery import (
        PolarsBigQueryIOManager,  # noqa
        PolarsBigQueryTypeHandler,  # noqa
    )

    __all__.extend(["PolarsBigQueryIOManager", "PolarsBigQueryTypeHandler"])
except ImportError as e:
    if "google-cloud-bigquery" in str(e):
        pass
    else:
        raise e
