import os
import subprocess
import time
from contextlib import contextmanager

import grpc
import pytest
from dagster_test.dagster_core_docker_buildkite import (
    build_and_tag_test_image,
    test_project_docker_image,
)

from dagster import check
from dagster.grpc.client import DagsterGrpcClient
from dagster.utils import file_relative_path

IS_BUILDKITE = os.getenv('BUILDKITE') is not None
HARDCODED_PORT = 8090


@pytest.fixture(scope='session')
def dagster_docker_image():
    docker_image = test_project_docker_image()

    if not IS_BUILDKITE:
        # Being conservative here when first introducing this. This could fail
        # if the Docker daemon is not running, so for now we just skip the tests using this
        # fixture if the build fails, and warn with the output from the build command
        try:
            build_and_tag_test_image(docker_image)
        except subprocess.CalledProcessError as exc_info:
            pytest.skip(
                "Skipped container tests due to a failure when trying to build the image. "
                "Most likely, the docker deamon is not running.\n"
                "Output:\n{}".format(exc_info.output.decode())
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

    assert retry_limit == 0
    raise Exception(
        'too many retries for grpc_server at {host}:{port}'.format(host=host, port=port)
    )


@contextmanager
def docker_service_up(docker_compose_file, service_name):
    check.str_param(service_name, 'service_name')
    check.str_param(docker_compose_file, 'docker_compose_file')
    check.invariant(
        os.path.isfile(docker_compose_file), 'docker_compose_file must specify a valid file'
    )

    if not IS_BUILDKITE:
        env = os.environ.copy()
        env["IMAGE_NAME"] = test_project_docker_image()

        try:
            subprocess.check_output(
                ['docker-compose', '-f', docker_compose_file, 'stop', service_name], env=env,
            )
            subprocess.check_output(
                ['docker-compose', '-f', docker_compose_file, 'rm', '-f', service_name], env=env,
            )
        except Exception:  # pylint: disable=broad-except
            pass

        subprocess.check_output(
            ['docker-compose', '-f', docker_compose_file, 'up', '-d', service_name], env=env,
        )

    yield


@pytest.fixture(scope='session')
def grpc_host():
    # In buildkite we get the ip address from this variable (see buildkite code for commentary)
    # Otherwise assume local development and assume localhost
    env_name = 'GRPC_SERVER_HOST'
    if env_name not in os.environ:
        os.environ[env_name] = 'localhost'
    return os.environ[env_name]


@pytest.fixture(scope='session')
def grpc_port():
    yield HARDCODED_PORT


@pytest.fixture(scope='session')
def docker_grpc_client(
    dagster_docker_image, grpc_host, grpc_port
):  # pylint: disable=redefined-outer-name, unused-argument
    if not IS_BUILDKITE:
        docker_service_up(file_relative_path(__file__, 'docker-compose.yml'), 'dagster-grpc-server')

    wait_for_connection(grpc_host, grpc_port)
    yield DagsterGrpcClient(port=grpc_port, host=grpc_host)
