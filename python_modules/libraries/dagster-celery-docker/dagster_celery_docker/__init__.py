from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_celery_docker.executor import celery_docker_executor as celery_docker_executor
from dagster_celery_docker.version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-celery-docker", __version__)
