from dagster._core.libraries import DagsterLibraryRegistry

from .version import __version__
from .executor import celery_executor

DagsterLibraryRegistry.register("dagster-celery", __version__)

__all__ = ["celery_executor"]
