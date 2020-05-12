from dagster.core.utils import check_dagster_package_version

from .executor import dask_executor
from .version import __version__

check_dagster_package_version('dagster-dask', __version__)

__all__ = ['dask_executor']
