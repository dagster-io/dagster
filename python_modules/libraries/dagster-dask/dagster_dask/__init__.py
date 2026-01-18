from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_dask.data_frame import DataFrame as DataFrame
from dagster_dask.executor import dask_executor as dask_executor
from dagster_dask.resources import dask_resource as dask_resource
from dagster_dask.version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-dask", __version__)
