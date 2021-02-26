import os
import subprocess
import sys
import time
from contextlib import contextmanager

import docker
import grpc
import pytest
from dagster import check, seven
from dagster.grpc.client import DagsterGrpcClient
from dagster.seven import nullcontext
from dagster.utils import file_relative_path
from dagster_test.dagster_core_docker_buildkite import (
    build_and_tag_test_image,
    get_test_project_docker_image,
)

IS_BUILDKITE = os.getenv("BUILDKITE") is not None
HARDCODED_PORT = 8090

# Suggested workaround in https://bugs.python.org/issue37380 for subprocesses
# failing to open sporadically on windows after other subprocesses were closed.
# Fixed in later versions of Python but never back-ported, see the bug for details.
if seven.IS_WINDOWS and sys.version_info[0] == 3 and sys.version_info[1] == 6:
    subprocess._cleanup = lambda: None  # type: ignore # pylint: disable=protected-access


@pytest.fixture(scope="session")
def dagster_docker_image():
    docker_image = get_test_project_docker_image()

    if not IS_BUILDKITE:
        # Being conservative here when first introducing this. This could fail
        # if the Docker daemon is not running, so for now we just skip the tests using this
        # fixture if the build fails, and warn with the output from the build command
        try:
            client = docker.from_env()
            client.images.get(docker_image)
            print(  # pylint: disable=print-call
                "Found existing image tagged {image}, skipping image build. To rebuild, first run: "
                "docker rmi {image}".format(image=docker_image)
            )
        except docker.errors.ImageNotFound:
            try:
                build_and_tag_test_image(docker_image)
            except subprocess.CalledProcessError as exc_info:
                pytest.skip(
                    "Skipped container tests due to a failure when trying to build the image. "
                    "Most likely, the docker deamon is not running.\n"
                    "Output:\n{}".format(exc_info.output.decode("utf-8"))
                )

    return docker_image


def wait_for_connection(host, port):
    retry_limit = 20

    while retry_limit:
        try:
            if DagsterGrpcClient(host=host, port=port).ping("ready") == "ready":
                return True
        except grpc.RpcError:
            pass

        time.sleep(0.2)
        retry_limit -= 1

    pytest.skip(
        "Skipped grpc container tests due to a failure when trying to connect to the GRPC server "
        "at {host}:{port}".format(host=host, port=port)
    )


@contextmanager
def docker_service_up(docker_compose_file, service_name):
    check.str_param(service_name, "service_name")
    check.str_param(docker_compose_file, "docker_compose_file")
    check.invariant(
        os.path.isfile(docker_compose_file), "docker_compose_file must specify a valid file"
    )

    if not IS_BUILDKITE:
        env = os.environ.copy()
        env["IMAGE_NAME"] = get_test_project_docker_image()

        try:
            subprocess.check_output(
                ["docker-compose", "-f", docker_compose_file, "stop", service_name],
                env=env,
            )
            subprocess.check_output(
                ["docker-compose", "-f", docker_compose_file, "rm", "-f", service_name],
                env=env,
            )
        except Exception:  # pylint: disable=broad-except
            pass

        subprocess.check_output(
            ["docker-compose", "-f", docker_compose_file, "up", "-d", service_name],
            env=env,
        )

        yield

        try:
            subprocess.check_output(
                ["docker-compose", "-f", docker_compose_file, "stop", service_name],
                env=env,
            )
            subprocess.check_output(
                ["docker-compose", "-f", docker_compose_file, "rm", "-f", service_name],
                env=env,
            )
        except Exception:  # pylint: disable=broad-except
            pass


@pytest.fixture(scope="session")
def grpc_host():
    # In buildkite we get the ip address from this variable (see buildkite code for commentary)
    # Otherwise assume local development and assume localhost
    env_name = "GRPC_SERVER_HOST"
    if env_name not in os.environ:
        os.environ[env_name] = "localhost"
    return os.environ[env_name]


@pytest.fixture(scope="session")
def grpc_port():
    yield HARDCODED_PORT


@pytest.fixture(scope="session")
def docker_grpc_client(
    dagster_docker_image, grpc_host, grpc_port
):  # pylint: disable=redefined-outer-name, unused-argument
    with docker_service_up(
        file_relative_path(__file__, "docker-compose.yml"), "dagster-grpc-server"
    ) if not IS_BUILDKITE else nullcontext():
        wait_for_connection(grpc_host, grpc_port)
        yield DagsterGrpcClient(port=grpc_port, host=grpc_host)
