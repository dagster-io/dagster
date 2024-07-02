from dagster._core.libraries import DagsterLibraryRegistry

from .version import __version__ as __version__
from .executor import dask_executor as dask_executor
from .resources import dask_resource as dask_resource
from .data_frame import DataFrame as DataFrame

DagsterLibraryRegistry.register("dagster-dask", __version__)
