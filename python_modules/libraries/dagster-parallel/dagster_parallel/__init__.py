from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_parallel.resource import ParallelSearchResource, ParallelSearchResult
from dagster_parallel.version import __version__

DagsterLibraryRegistry.register("dagster-parallel", __version__)

__all__ = ["ParallelSearchResource", "ParallelSearchResult"]
