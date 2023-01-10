from dagster._core.utils import check_dagster_package_version

from .data_frame import DataFrame as DataFrame
from .executor import dask_executor as dask_executor
from .resources import dask_resource as dask_resource
from .version import __version__ as __version__

check_dagster_package_version("dagster-dask", __version__)
