from dagster_celery.executor import celery_executor
from dagster_celery.version import __version__
from dagster_shared.libraries import DagsterLibraryRegistry

DagsterLibraryRegistry.register("dagster-celery", __version__)

__all__ = ["celery_executor"]
