from dagster.core.utils import check_dagster_package_version

from .data_frame import DataFrame
from .executor import dask_executor
from .resources import dask_resource
from .version import __version__

check_dagster_package_version("dagster-dask", __version__)

__all__ = [
    "DataFrame",
    "dask_executor",
]
