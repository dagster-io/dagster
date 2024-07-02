from dagster._core.libraries import DagsterLibraryRegistry

from .version import __version__ as __version__
from .executor import celery_docker_executor as celery_docker_executor

DagsterLibraryRegistry.register("dagster-celery-docker", __version__)
