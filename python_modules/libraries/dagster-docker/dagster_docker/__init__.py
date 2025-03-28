from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_docker.docker_executor import docker_executor as docker_executor
from dagster_docker.docker_run_launcher import DockerRunLauncher as DockerRunLauncher
from dagster_docker.ops import (
    docker_container_op as docker_container_op,
    execute_docker_container as execute_docker_container,
)
from dagster_docker.pipes import (
    PipesDockerClient as PipesDockerClient,
    PipesDockerLogsMessageReader as PipesDockerLogsMessageReader,
)
from dagster_docker.version import __version__

DagsterLibraryRegistry.register("dagster-docker", __version__)
