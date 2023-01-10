from dagster._core.utils import check_dagster_package_version

from .executor import celery_docker_executor as celery_docker_executor
from .version import __version__ as __version__

check_dagster_package_version("dagster-celery-docker", __version__)
