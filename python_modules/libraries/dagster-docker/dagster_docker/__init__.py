from dagster._core.utils import check_dagster_package_version

from .docker_executor import docker_executor as docker_executor
from .docker_run_launcher import DockerRunLauncher as DockerRunLauncher
from .ops import (
    docker_container_op as docker_container_op,
    execute_docker_container as execute_docker_container,
)
from .version import __version__

check_dagster_package_version("dagster-docker", __version__)
