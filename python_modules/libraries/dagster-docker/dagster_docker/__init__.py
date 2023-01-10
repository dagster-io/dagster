from dagster._core.utils import check_dagster_package_version

from .docker_executor import docker_executor as docker_executor
from .docker_run_launcher import DockerRunLauncher as DockerRunLauncher
from .version import __version__

check_dagster_package_version("dagster-docker", __version__)
