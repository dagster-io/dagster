from dagster._core.libraries import DagsterLibraryRegistry

from .executor import celery_executor
from .version import __version__

DagsterLibraryRegistry.register("dagster-celery", __version__)

__all__ = ["celery_executor"]
